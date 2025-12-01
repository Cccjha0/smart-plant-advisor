"""
工作流服务 - 调用Coze工作流API进行AI分析
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from cozepy import Coze, TokenAuth, COZE_COM_BASE_URL
    from cozepy.exception import CozeAPIError
    import requests
    COZEPY_AVAILABLE = True
except ImportError:
    COZEPY_AVAILABLE = False
    CozeAPIError = None
    requests = None


class WorkflowService:
    """工作流服务 - 调用Coze工作流API"""
    
    def __init__(self):
        if not COZEPY_AVAILABLE:
            raise ImportError("cozepy 未安装。请运行: pip install cozepy")
        
        self.coze_api_token = os.getenv("COZE_API_TOKEN")
        self.workflow_id = os.getenv("COZE_WORKFLOW_ID")
        # 确保使用国际版API（如果未设置，默认使用国际版）
        self.coze_api_base = os.getenv("COZE_API_BASE", COZE_COM_BASE_URL)

        # 中国区工作流（梦境图片）配置
        self.coze_api_token_cn = os.getenv("COZE_API_TOKEN_CN")
        self.workflow_id_cn = os.getenv("COZE_WORKFLOW_ID_CN")
        self.coze_api_base_cn = os.getenv("COZE_API_BASE_CN", "https://api.coze.cn")

        # 中国区工作流（梦境图片）配置：独立的 token / workflow / base url
        self.coze_api_token_cn = os.getenv("COZE_API_TOKEN_CN")
        self.workflow_id_cn = os.getenv("COZE_WORKFLOW_ID_CN")
        self.coze_api_base_cn = os.getenv("COZE_API_BASE_CN", "https://api.coze.cn")
        
        # 如果误配置为中国区，强制使用国际版
        if "coze.cn" in self.coze_api_base:
            print(f"警告: 检测到中国区API ({self.coze_api_base})，自动切换为国际版")
            self.coze_api_base = COZE_COM_BASE_URL
        
        # 可选参数：如果工作流需要关联bot或app
        self.bot_id = os.getenv("COZE_BOT_ID")  # 如果工作流包含数据库节点、变量节点等，可能需要
        self.app_id = os.getenv("COZE_APP_ID")  # 如果在app中执行工作流，需要指定
        
        if not self.coze_api_token:
            raise ValueError("COZE_API_TOKEN 环境变量未设置")
        if not self.workflow_id:
            raise ValueError("COZE_WORKFLOW_ID 环境变量未设置")
        
        # 初始化Coze客户端
        self.coze = Coze(
            auth=TokenAuth(token=self.coze_api_token),
            base_url=self.coze_api_base
        )

        self.coze_cn = None
        if self.coze_api_token_cn and self.workflow_id_cn:
            try:
                self.coze_cn = Coze(
                    auth=TokenAuth(token=self.coze_api_token_cn),
                    base_url=self.coze_api_base_cn,
                )
            except Exception as e:
                print(f"警告: 初始化中国区 Coze 客户端失败，将跳过 CN 工作流。err={e}")
                self.coze_cn = None
        
        self._is_configured = True
    
    def _call_workflow_with_retry(
        self,
        workflow_inputs: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: int = 2,
        *,
        workflow_id: Optional[str] = None,
        coze_client=None,
        bot_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ):
        """
        调用工作流，带重试机制（处理VPN不稳定问题）
        
        Args:
            workflow_inputs: 工作流输入参数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            workflow_id: 覆盖默认工作流ID
            coze_client: 覆盖默认Coze客户端
            bot_id/app_id: 覆盖默认bot/app
            
        Returns:
            WorkflowRunResult对象
        """
        import time

        wf_id = workflow_id or self.workflow_id
        client = coze_client or self.coze
        bot = bot_id if bot_id is not None else self.bot_id
        app = app_id if app_id is not None else self.app_id
        
        for attempt in range(max_retries):
            try:
                workflow_run = client.workflows.runs.create(
                    workflow_id=wf_id,
                    parameters=workflow_inputs,
                    bot_id=bot if bot else None,
                    app_id=app if app else None,
                )
                return workflow_run
            except CozeAPIError as e:
                # Coze API特定错误
                if e.code in [720701013] or (e.msg and "server issues" in e.msg.lower()):
                    if attempt < max_retries - 1:
                        print(f"⚠️ Coze服务器暂时不可用，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})... (错误: {e.msg})")
                        time.sleep(retry_delay)
                        continue
                # 其他Coze API错误（如token无效、参数错误等）不重试
                raise
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # 网络连接错误
                if attempt < max_retries - 1:
                    print(f"⚠️ 网络连接错误，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})... (错误: {str(e)})")
                    time.sleep(retry_delay)
                    continue
                raise
            except Exception as e:
                # 其他未知错误，不重试
                raise
    
    def _format_sensor_data_to_text(self, sensor_data: Dict[str, Any]) -> str:
        """
        将传感器数据格式化为工作流需要的文本格式
        例如: "temp=25.6, humidity=60, soil=32, light=1180"
        
        Args:
            sensor_data: 传感器数据字典
            
        Returns:
            格式化的文本字符串
        """
        parts = []
        
        # 温度
        temp = sensor_data.get("temperature") or sensor_data.get("avg_temperature")
        if temp is not None:
            parts.append(f"temp={temp}")
        
        # 湿度（如果有）
        humidity = sensor_data.get("humidity") or sensor_data.get("avg_humidity")
        if humidity is not None:
            parts.append(f"humidity={humidity}")
        
        # 土壤湿度
        soil = sensor_data.get("soil_moisture") or sensor_data.get("avg_soil_moisture")
        if soil is not None:
            parts.append(f"soil={soil}")
        
        # 光照
        light = sensor_data.get("light") or sensor_data.get("avg_light")
        if light is not None:
            parts.append(f"light={light}")

        return ", ".join(parts)

    def generate_dream_image_cn(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """
        调用中国区 Coze 梦境花园工作流。

        预期输入字段（全部字符串）:
          - plant_id
          - temperature
          - light
          - soil_moisture
          - health_status

        返回字段:
          - output: 图片（字符串，取决于工作流定义，例如 base64 或 URL）
          - msg: 文本提示
          - raw_response: 原始返回，便于调试
        """
        if not (self.coze_cn and self.workflow_id_cn):
            raise ValueError("中国区 Coze 工作流未配置，请设置 COZE_API_TOKEN_CN / COZE_WORKFLOW_ID_CN")

        workflow_inputs = {
            "plant_id": str(payload.get("plant_id", "")),
            "temperature": str(payload.get("temperature", "")),
            "light": str(payload.get("light", "")),
            "soil_moisture": str(payload.get("soil_moisture", "")),
            "health_status": str(payload.get("health_status", "")),
        }

        workflow_run = self._call_workflow_with_retry(
            workflow_inputs,
            workflow_id=self.workflow_id_cn,
            coze_client=self.coze_cn,
            bot_id=None,
            app_id=None,
        )

        result_data = workflow_run.data if hasattr(workflow_run, "data") else None
        if result_data is None:
            raise Exception("梦境工作流返回数据为空")

        if isinstance(result_data, dict):
            output = result_data.get("output")
            msg = result_data.get("msg")
            parsed = result_data
        else:
            output = None
            msg = str(result_data)
            parsed = {"raw": result_data}

        return {
            "output": output,
            "msg": msg,
            "raw_response": parsed,
        }
    
    def analyze_plant(
        self,
        image_url: str,
        sensor_data: Dict[str, Any],
        plant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用Coze工作流API进行植物分析
        
        Args:
            image_url: 植物图片的云存储URL
            sensor_data: 传感器数据字典，包含：
                - temperature: 温度
                - light: 光照
                - soil_moisture: 土壤湿度
                - 其他传感器数据...
            plant_id: 植物ID（可选，用于日志）
            
        Returns:
            分析结果字典，包含：
                - plant_type: 植物类型
                - leaf_health: 叶片健康状态
                - symptoms: 症状列表
                - 其他分析结果...
        """
        if not self._is_configured:
            raise ValueError("工作流API未配置。请设置 COZE_API_TOKEN 和 COZE_WORKFLOW_ID 环境变量")
        
        # 格式化传感器数据为文本
        sensor_text = self._format_sensor_data_to_text(sensor_data)
        
        # 构建工作流输入参数（使用Coze工作流要求的参数名称）
        workflow_inputs = {
            "userUploadedImage": image_url,
            "userMessageText": sensor_text,
        }
        
        try:
            # 调用Coze工作流（非流式响应，带重试机制处理VPN不稳定）
            # 注意：工作流必须已发布才能通过API执行
            # 如果工作流包含数据库节点、变量节点等，可能需要指定 bot_id
            # 如果在app中执行，需要指定 app_id
            # 不能同时指定 bot_id 和 app_id
            workflow_run = self._call_workflow_with_retry(workflow_inputs)
            
            # 获取工作流运行结果
            result_data = workflow_run.data if hasattr(workflow_run, 'data') else None
            
            if result_data is None:
                raise Exception("工作流返回数据为空")
            
            # 如果结果是字符串，尝试解析为JSON
            parsed_data = None
            if isinstance(result_data, str):
                import json
                try:
                    parsed_data = json.loads(result_data)
                except json.JSONDecodeError:
                    # 如果不是JSON，直接使用字符串
                    parsed_data = {"final_output": result_data}
            elif isinstance(result_data, dict):
                parsed_data = result_data
            else:
                parsed_data = {"final_output": str(result_data)}
            
            # 从解析后的数据中提取信息
            final_output = parsed_data.get("final_output", "")
            
            # 尝试从final_output中提取结构化信息（如果工作流返回的是文本）
            plant_type = parsed_data.get("plant_type") or None
            leaf_health = parsed_data.get("leaf_health") or None
            symptoms = parsed_data.get("symptoms", [])
            
            # 如果final_output包含信息，可以尝试简单提取（可选）
            if final_output and not plant_type:
                # 简单提取植物类型（如果工作流输出中包含）
                if "jasmine" in final_output.lower():
                    plant_type = "Jasmine"
                # 可以根据需要添加更多提取逻辑
            
            # 标准化返回格式
            return {
                "plant_type": plant_type,
                "leaf_health": leaf_health,
                "symptoms": symptoms if isinstance(symptoms, list) else [],
                "report_short": parsed_data.get("report_short"),
                "report_long": parsed_data.get("report_long") or final_output,
                "raw_response": parsed_data,  # 保留原始响应以便调试
            }
            
        except Exception as e:
            # 提供更详细的错误信息
            error_msg = str(e)
            
            # 检查是否是Coze API错误
            if hasattr(e, 'code'):
                if e.code == 700012006:
                    msg = getattr(e, 'msg', '')
                    if 'expired' in msg.lower():
                        error_msg = f"访问令牌已过期（错误码: {e.code}）。请在Coze平台重新生成Token并更新.env文件中的COZE_API_TOKEN。"
                    elif 'invalid' in msg.lower():
                        error_msg = f"访问令牌无效（错误码: {e.code}）。请检查Token是否正确，或重新生成Token。确保使用Personal Access Token而不是其他类型的token。"
                    else:
                        error_msg = f"访问令牌错误（错误码: {e.code}）: {msg}。请检查Token是否正确。"
                elif e.code == 720701013:
                    error_msg = f"Coze服务器暂时不可用（错误码: {e.code}）。请稍后重试。如果问题持续，请联系Coze技术支持。"
                elif e.code == 4200:
                    error_msg = f"工作流未发布（错误码: {e.code}）。请在Coze平台发布工作流后再试。"
                elif e.code == 4000:
                    error_msg = f"请求参数错误（错误码: {e.code}）。请检查工作流参数定义。调试URL: {getattr(e, 'debug_url', 'N/A')}"
                else:
                    error_msg = f"工作流API调用失败（错误码: {e.code}）: {getattr(e, 'msg', error_msg)}"
            
            raise Exception(error_msg)
    

    def analyze_with_growth_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call workflow with a full JSON payload (already merged metrics, sensors, stress).
        Expected payload keys example:
        {
            "growth_rate_3d": ...,
            "growth_status": ...,
            "image_url": ...,
            "metrics_snapshot": {...},
            "nickname": ...,
            "plant_id": ...,
            "sensor_data": {...},
            "stress_factors": {...}
        }
        """
        if not self._is_configured:
            raise ValueError("工作流API未配置。请设置 COZE_API_TOKEN 和 COZE_WORKFLOW_ID")

        workflow_inputs = payload

        try:
            workflow_run = self._call_workflow_with_retry(workflow_inputs)
            result_data = workflow_run.data if hasattr(workflow_run, 'data') else None
            if result_data is None:
                raise Exception("工作流返回数据为空")

            if isinstance(result_data, str):
                try:
                    parsed_data = json.loads(result_data)
                except json.JSONDecodeError:
                    parsed_data = {"final_output": result_data}
            elif isinstance(result_data, dict):
                parsed_data = result_data
            else:
                parsed_data = {"final_output": str(result_data)}

            final_output = parsed_data.get("final_output", "")

            return {
                "plant_type": parsed_data.get("plant_type"),
                "growth_overview": parsed_data.get("growth_overview"),
                "environment_assessment": parsed_data.get("environment_assessment"),
                "suggestions": parsed_data.get("suggestions"),
                "full_analysis": parsed_data.get("full_analysis") or final_output,
                "alert": parsed_data.get("alert"),
                "analysis_json": parsed_data.get("analysis_json"),
                "raw_response": parsed_data,
            }

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'code'):
                if e.code == 700012006:
                    msg = getattr(e, 'msg', '')
                    if 'expired' in msg.lower():
                        error_msg = f"访问令牌已过期（错误码: {e.code}）。请在Coze平台重新生成Token并更新.env中的COZE_API_TOKEN"
                    elif 'invalid' in msg.lower():
                        error_msg = f"访问令牌无效（错误码: {e.code}）。请检查Token是否正确，或重新生成Token。确保使用Personal Access Token"
                    else:
                        error_msg = f"访问令牌错误（错误码: {e.code}，{msg}）。请检查Token是否正确"
                elif e.code == 720701013:
                    error_msg = f"Coze服务器暂不可用（错误码: {e.code}）。请稍后重试。如问题持续，请联系Coze技术支持。"
                elif e.code == 4200:
                    error_msg = f"工作流未发布（错误码: {e.code}）。请在Coze平台发布工作流后再试。"
                elif e.code == 4000:
                    error_msg = f"请求参数错误（错误码: {e.code}）。请检查工作流参数定义。调试URL: {getattr(e, 'debug_url', 'N/A')}"
                else:
                    error_msg = f"工作流API调用失败（错误码: {e.code}，{getattr(e, 'msg', error_msg)}）"

            raise Exception(error_msg)


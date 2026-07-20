"""异常定义"""


class AppError(Exception):
    """应用基础异常"""


class NotFoundError(AppError):
    """资源未找到"""


class ValidationError(AppError):
    """数据验证失败"""


class NetworkError(AppError):
    """网络请求失败"""

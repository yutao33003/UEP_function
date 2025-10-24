# overlay_factory.py
class OverlayFactory:
    _registry = {}
    _instances = {}

    @classmethod
    def register(cls, name: str, overlay_cls):
        cls._registry[name] = overlay_cls

    @classmethod
    def create(cls, key: str, *args, scope=None, cache=False, **kwargs):
        """
        建立或取得 overlay 實體。
        - key: 註冊名稱
        - scope: 群組名稱（例如 "abc"、"edf"）
        - cache=True: 同一 scope + key 共用 overlay
        """
        if key not in cls._registry:
            raise ValueError(f"No overlay registered under key '{key}'")

        overlay_class = cls._registry[key]
        instance_key = f"{scope}:{key}" if scope else key

        if cache and instance_key in cls._instances:
            instance = cls._instances[instance_key]
            if hasattr(instance, "refresh"):
                instance.refresh(*args, **kwargs)
            return instance

        instance = overlay_class(*args, **kwargs)

        if cache:
            cls._instances[instance_key] = instance

        return instance

    @classmethod
    def clear_scope(cls, scope: str):
        """移除整個群組的 overlay 實例"""
        to_delete = [k for k in cls._instances if k.startswith(f"{scope}:")]
        for k in to_delete:
            del cls._instances[k]
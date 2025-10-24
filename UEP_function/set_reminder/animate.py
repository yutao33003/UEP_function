from PyQt5.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsOpacityEffect


def gradually_enter_ani(container, duration=500):
    effect = QGraphicsOpacityEffect(container)
    container.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    animation = QPropertyAnimation(effect, b"opacity", container)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    container._fade_in_animation = animation
    animation.start()

def gradually_exit_ani(container, duration=800, finished_callback=None):
    """
    漸出效果（fade out），動畫結束後可執行 callback
    """
    # 設置透明效果
    effect = container.graphicsEffect()
    if not effect or not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(container)
        container.setGraphicsEffect(effect)
    effect.setOpacity(1.0)

    # 建立動畫
    animation = QPropertyAnimation(effect, b"opacity", container)
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    # 結束時執行 callback（例如 close）
    if finished_callback:
        animation.finished.connect(finished_callback)

    # 避免被垃圾回收
    container._fade_out_animation = animation
    animation.start()

def delete_with_animation(widget, on_deleted=None):

    anim_group = QParallelAnimationGroup(widget)

    # 淡出動畫
    opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
    opacity_anim.setDuration(300)
    opacity_anim.setStartValue(1.0)
    opacity_anim.setEndValue(0.0)
    anim_group.addAnimation(opacity_anim)

    # 收縮動畫
    size_anim = QPropertyAnimation(widget, b"maximumHeight")
    size_anim.setDuration(300)
    size_anim.setStartValue(widget.height())
    size_anim.setEndValue(0)
    size_anim.setEasingCurve(QEasingCurve.InOutCubic)
    anim_group.addAnimation(size_anim)
    def on_finished():
        parent_layout = widget.parentWidget().layout()
        if parent_layout is not None:
            parent_layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        if on_deleted:
            on_deleted()  # 如果有額外動作就執行

    anim_group.finished.connect(on_finished)
    anim_group.start()
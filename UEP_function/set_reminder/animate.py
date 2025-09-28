from PyQt5.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsOpacityEffect


def gradually_enter_ani(self, container, duration=800):
    self.opacity_effect = QGraphicsOpacityEffect(container)
    container.setGraphicsEffect(self.opacity_effect)

    self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    self.fade_in_animation.setDuration(duration)  # 800 毫秒
    self.fade_in_animation.setStartValue(0.0)
    self.fade_in_animation.setEndValue(1.0)
    self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
    self.fade_in_animation.start()

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
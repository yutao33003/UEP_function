from PyQt5.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QPoint
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
    effect = container.graphicsEffect()
    if not effect or not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(container)
        container.setGraphicsEffect(effect)
    effect.setOpacity(1.0)

    animation = QPropertyAnimation(effect, b"opacity", container)
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    if finished_callback:
        animation.finished.connect(finished_callback)

    container._fade_out_animation = animation
    animation.start()


def delete_with_animation(widget, on_deleted=None):
    """
    安全地對 widget 做淡出 + 高度收縮動畫，動畫結束後移除並 deleteLater。
    若 widget 已被底層刪除或在建立動畫時發生錯誤，會 fallback 為同步移除並呼叫 on_deleted。
    """
    if widget is None:
        if on_deleted:
            on_deleted()
        return

    # 快速檢查：若 wrapper 已被底層刪除（訪問 parentWidget 會 raise），則 fallback
    try:
        _ = widget.parentWidget()
    except RuntimeError:
        # 已被刪除或不可存取
        try:
            if on_deleted:
                on_deleted()
        except Exception:
            pass
        return

    # 選一個安全的 parent 當作 animation group 的父物件（避免直接以被刪除的 widget 當父）
    try:
        anim_parent = widget.parentWidget() or widget.window() or None
    except Exception:
        anim_parent = None

    try:
        anim_group = QParallelAnimationGroup(anim_parent)
    except Exception:
        anim_group = QParallelAnimationGroup()

    # 建立兩個動畫；任何時候若 widget 在建立動畫時被刪除，會捕捉例外並作 fallback
    try:
        opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        anim_group.addAnimation(opacity_anim)

        size_anim = QPropertyAnimation(widget, b"maximumHeight")
        size_anim.setDuration(300)
        size_anim.setStartValue(widget.height())
        size_anim.setEndValue(0)
        size_anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim_group.addAnimation(size_anim)
    except Exception:
        # widget 可能在此刻被刪除，作同步清理並呼叫 callback
        try:
            parent_layout = widget.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(widget)
        except Exception:
            pass
        try:
            widget.setParent(None)
            widget.deleteLater()
        except Exception:
            pass
        if on_deleted:
            try:
                on_deleted()
            except Exception:
                pass
        return

    def _on_finished():
        try:
            parent_layout = widget.parentWidget().layout()
            if parent_layout is not None:
                parent_layout.removeWidget(widget)
        except Exception:
            pass
        try:
            widget.setParent(None)
            widget.deleteLater()
        except Exception:
            pass
        if on_deleted:
            try:
                on_deleted()
            except Exception:
                pass

    anim_group.finished.connect(_on_finished)
    # 保留 reference 防止被 GC
    try:
        widget._delete_anim = anim_group
    except Exception:
        pass
    anim_group.start()


def slide_stack(stack, new_index, direction='left', duration=500):
    if not stack:
        return
    cur_index = stack.currentIndex()
    if cur_index == new_index:
        return
    try:
        cur_widget = stack.widget(cur_index)
        new_widget = stack.widget(new_index)
    except Exception:
        stack.setCurrentIndex(new_index)
        return

    stack_rect = stack.geometry()
    w = stack_rect.width()
    h = stack_rect.height()
    if w == 0 or h == 0:
        stack.setCurrentIndex(new_index)
        return

    if direction == 'left':
        start_new = QPoint(w, 0)
        end_new = QPoint(0, 0)
        start_cur = QPoint(0, 0)
        end_cur = QPoint(-w, 0)
    else:
        start_new = QPoint(-w, 0)
        end_new = QPoint(0, 0)
        start_cur = QPoint(0, 0)
        end_cur = QPoint(w, 0)

    new_widget.setGeometry(0, 0, w, h)
    new_widget.move(start_new)
    new_widget.show()
    new_widget.raise_()
    cur_widget.raise_()

    anim_group = QParallelAnimationGroup(stack)

    anim_new = QPropertyAnimation(new_widget, b"pos")
    anim_new.setDuration(duration)
    anim_new.setStartValue(start_new)
    anim_new.setEndValue(end_new)
    anim_new.setEasingCurve(QEasingCurve.InOutCubic)
    anim_group.addAnimation(anim_new)

    anim_cur = QPropertyAnimation(cur_widget, b"pos")
    anim_cur.setDuration(duration)
    anim_cur.setStartValue(start_cur)
    anim_cur.setEndValue(end_cur)
    anim_cur.setEasingCurve(QEasingCurve.InOutCubic)
    anim_group.addAnimation(anim_cur)

    def on_finished():
        stack.setCurrentIndex(new_index)
        try:
            new_widget.move(0, 0)
            cur_widget.move(0, 0)
        except Exception:
            pass
        if hasattr(stack, "_slide_animation"):
            delattr(stack, "_slide_animation")

    anim_group.finished.connect(on_finished)
    stack._slide_animation = anim_group
    anim_group.start()
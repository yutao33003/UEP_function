from PyQt5.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QPoint
from PyQt5.QtWidgets import QGraphicsOpacityEffect


def gradually_enter_ani(container, duration=500):
    """
    漸入（fade in）某個 container（通常為內容 widget，不是整個遮罩）。
    """
    effect = QGraphicsOpacityEffect(container)
    container.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    animation = QPropertyAnimation(effect, b"opacity", container)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.InOutQuad)

    # 保持參考，避免被 GC
    container._fade_in_animation = animation
    animation.start()


def gradually_exit_ani(container, duration=800, finished_callback=None):
    """
    漸出（fade out），動畫結束後可執行 callback（例如 close）。
    """
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
    anim_group = QParallelAnimationGroup(widget)

    # 淡出動畫（視窗 opacity）
    opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
    opacity_anim.setDuration(300)
    opacity_anim.setStartValue(1.0)
    opacity_anim.setEndValue(0.0)
    anim_group.addAnimation(opacity_anim)

    # 收縮動畫（最大高度）
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
            on_deleted()

    anim_group.finished.connect(on_finished)
    anim_group.start()


def slide_stack(stack, new_index, direction='left', duration=500):
    """
    使用左右滑動在 QStackedWidget 中切換頁面。
    - stack: QStackedWidget
    - new_index: 目標 index
    - direction: 'left' (新頁由右往左進入) 或 'right' (新頁由左往右進入)
    會自動處理 widget 的位置與動畫，動畫結束後設置 stack.currentIndex(new_index)。
    """
    if not stack:
        return
    cur_index = stack.currentIndex()
    if cur_index == new_index:
        return

    # 取得 widget
    try:
        cur_widget = stack.widget(cur_index)
        new_widget = stack.widget(new_index)
    except Exception:
        stack.setCurrentIndex(new_index)
        return

    # geometry 與初始位置（在 stack 的座標系）
    stack_rect = stack.geometry()
    w = stack_rect.width()
    h = stack_rect.height()

    # 若大小為 0 則直接切換
    if w == 0 or h == 0:
        stack.setCurrentIndex(new_index)
        return

    # 計算位置（以 stack 客戶區域 (0,0) 為基準）
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

    # 確保 new_widget geometry 與顯示
    new_widget.setGeometry(0, 0, w, h)
    new_widget.move(start_new)
    new_widget.show()
    new_widget.raise_()
    cur_widget.raise_()

    # 動畫：移動 pos（保持在 stack 的座標系）
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
        # 切換 index 並重置位置
        stack.setCurrentIndex(new_index)
        try:
            new_widget.move(0, 0)
            cur_widget.move(0, 0)
        except Exception:
            pass
        # 清除暫存動畫引用
        if hasattr(stack, "_slide_animation"):
            delattr(stack, "_slide_animation")

    anim_group.finished.connect(on_finished)

    # 保持引用，避免 GC
    stack._slide_animation = anim_group
    anim_group.start()
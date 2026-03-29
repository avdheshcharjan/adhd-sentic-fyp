import AppKit
import SwiftUI

/// NSPanel overlay positioned at the hardware notch.
///
/// Design follows boring.notch and DynamicNotchKit:
/// - Fixed oversized frame (no resizing = no constraint cycles)
/// - `.mainMenu + 3` level (above menu bar, covers notch)
/// - `canBecomeKey/Main = false` (never steals focus)
/// - Clear background, no shadow (SwiftUI handles shadow)
/// - `.nonactivatingPanel` + `.borderless` style
class NotchWindow: NSPanel {

    /// Fixed canvas size — large enough for expanded state + shadow room.
    ///
    /// Width: 380 (expanded) + 60 shadow padding = 440
    /// Height: 280 (expanded, Paper spec) + 60 shadow padding = 340
    /// All other states (dormant 28px, ambient 28px, glanceable 36px, alert 80px)
    /// are smaller and fit inside this canvas.
    static let canvasSize = CGSize(
        width: ADHDSpacing.notchExpandedWidth + 60,
        height: ADHDSpacing.notchExpandedHeight + 60
    )

    /// Visible content dimensions per state — mirrors NotchContainerView's currentWidth/Height.
    static func contentSize(for state: NotchState) -> CGSize {
        switch state {
        case .dormant:    CGSize(width: ADHDSpacing.hardwareNotchWidth, height: ADHDSpacing.hardwareNotchHeight)
        case .ambient:    CGSize(width: ADHDSpacing.hardwareNotchWidth + 20, height: ADHDSpacing.hardwareNotchHeight)
        case .glanceable: CGSize(width: ADHDSpacing.notchGlanceWidth, height: ADHDSpacing.notchGlanceHeight)
        case .expanded:   CGSize(width: ADHDSpacing.notchExpandedWidth, height: ADHDSpacing.notchExpandedHeight)
        case .alert:      CGSize(width: ADHDSpacing.notchGlanceWidth, height: 80)
        }
    }

    init(contentView rootView: NSView) {
        let rect = NSRect(origin: .zero, size: Self.canvasSize)

        super.init(
            contentRect: rect,
            styleMask: [.borderless, .nonactivatingPanel, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        configurePanel()

        let canvas = NotchHitTestView(frame: rect)
        canvas.notchWindow = self
        rootView.frame = rect
        rootView.autoresizingMask = [.width, .height]
        canvas.addSubview(rootView)
        self.contentView = canvas

        positionAtNotch()

        // Reposition when screen configuration changes (display added/removed/rearranged)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(screenDidChange),
            name: NSApplication.didChangeScreenParametersNotification,
            object: nil
        )
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }

    @objc private func screenDidChange(_ notification: Notification) {
        positionAtNotch()
    }

    // MARK: - Focus behavior (DynamicNotchKit pattern)
    // canBecomeKey MUST be true for .onHover / NSTrackingArea to work.
    // .nonactivatingPanel prevents the panel from activating the app,
    // so this won't steal focus from the user's active window.

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

    /// The current visible notch size (updated by AppDelegate on state changes).
    /// Used by `isMousePoint(_:in:)` to restrict hit-testing to the notch shape.
    var visibleContentSize: CGSize = CGSize(width: ADHDSpacing.hardwareNotchWidth, height: ADHDSpacing.hardwareNotchHeight)

    /// Called when user clicks on the NotchWindow canvas area outside SwiftUI content.
    /// The global mouse monitor doesn't fire for our own panel, so this catches
    /// clicks on the transparent canvas surrounding the notch shape.
    var onClickAway: (() -> Void)?

    override func mouseDown(with event: NSEvent) {
        super.mouseDown(with: event)
        onClickAway?()
    }

    // MARK: - Hit-test by visible shape
    // Implemented in NotchHitTestView (the window's content view wrapper).
    // Points outside the visible notch region return nil from hitTest(_:),
    // so they pass through to apps below.

    // MARK: - Configuration

    private func configurePanel() {
        isFloatingPanel = true
        level = .mainMenu + 3              // Above menu bar, covers hardware notch
        isOpaque = false
        backgroundColor = .clear
        hasShadow = false                  // SwiftUI layer handles shadow
        titleVisibility = .hidden
        titlebarAppearsTransparent = true
        isMovable = false                  // Pinned in place
        acceptsMouseMovedEvents = true
        ignoresMouseEvents = false
        isReleasedWhenClosed = false
        appearance = NSAppearance(named: .darkAqua) // Force dark (notch is always dark)

        collectionBehavior = [
            .canJoinAllSpaces,             // Visible on all desktops
            .fullScreenAuxiliary,          // Visible alongside fullscreen apps
            .stationary,                   // Doesn't move with Spaces gestures
            .ignoresCycle,                 // Excluded from Cmd+Tab
        ]
    }

    // MARK: - Positioning

    func positionAtNotch() {
        // screens.first is the screen with the menu bar (and hardware notch).
        // NSScreen.main is the screen with the key window, which may differ.
        guard let screen = NSScreen.screens.first else { return }
        let screenFrame = screen.frame
        let x = screenFrame.midX - (Self.canvasSize.width / 2)
        let y = screenFrame.maxY - Self.canvasSize.height
        setFrame(
            NSRect(origin: NSPoint(x: x, y: y), size: Self.canvasSize),
            display: false
        )
    }

    /// Fade-in on first show (DynamicNotchKit pattern).
    func showWithFade() {
        alphaValue = 0
        orderFrontRegardless()
        NSAnimationContext.runAnimationGroup { ctx in
            ctx.duration = 0.15
            ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
            self.animator().alphaValue = 1
        }
    }
}
// MARK: - Hit-test passthrough view

/// Content-view wrapper that restricts hit-testing to the visible notch region.
/// Points outside the region return nil, letting events fall through to apps below.
private class NotchHitTestView: NSView {
    weak var notchWindow: NotchWindow?

    override func hitTest(_ point: NSPoint) -> NSView? {
        guard let win = notchWindow else { return super.hitTest(point) }

        let canvasW = bounds.width
        let canvasH = bounds.height
        let contentW = win.visibleContentSize.width
        let contentH = win.visibleContentSize.height

        // Notch is centered horizontally, pinned to top of canvas.
        // NSView coordinates: (0,0) is bottom-left, so top = high Y values.
        let minX = (canvasW - contentW) / 2
        let maxX = minX + contentW
        let minY = canvasH - contentH

        guard point.x >= minX && point.x <= maxX && point.y >= minY else {
            return nil // pass through to apps below
        }
        return super.hitTest(point)
    }
}


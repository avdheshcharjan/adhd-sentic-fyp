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
    static let canvasSize = CGSize(
        width: ADHDSpacing.notchExpandedWidth + 60,
        height: ADHDSpacing.notchExpandedHeight + 60
    )

    init(contentView rootView: NSView) {
        let rect = NSRect(origin: .zero, size: Self.canvasSize)

        super.init(
            contentRect: rect,
            styleMask: [.borderless, .nonactivatingPanel, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        configurePanel()
        self.contentView = rootView
        positionAtNotch()
    }

    // MARK: - Focus behavior (DynamicNotchKit pattern)
    // canBecomeKey MUST be true for .onHover / NSTrackingArea to work.
    // .nonactivatingPanel prevents the panel from activating the app,
    // so this won't steal focus from the user's active window.

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

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
        guard let screen = NSScreen.main else { return }
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

import AppKit
import SwiftUI

// MARK: - FloatingPanel

/// NSPanel subclass used for both the Brain Dump and Vent modals.
///
/// Design decisions:
/// - .nonactivatingPanel keeps the panel floating without stealing app focus
/// - .fullSizeContentView lets SwiftUI content render into the title bar area
/// - isReleasedWhenClosed = false preserves ViewModel state between toggles
/// - close() is overridden to hide instead of actually closing the window
final class FloatingPanel<Content: View>: NSPanel {

    // MARK: - Init

    init(contentRect: NSRect, content: Content) {
        super.init(
            contentRect: contentRect,
            styleMask: [
                .nonactivatingPanel,
                .titled,
                .closable,
                .fullSizeContentView,
            ],
            backing: .buffered,
            defer: false
        )

        isFloatingPanel = true
        level = .floating
        collectionBehavior = [.moveToActiveSpace, .fullScreenAuxiliary]

        titleVisibility = .hidden
        titlebarAppearsTransparent = true

        isMovableByWindowBackground = true
        isReleasedWhenClosed = false

        isOpaque = false
        backgroundColor = .clear
        hasShadow = true

        let hostingView = NSHostingView(rootView: content)
        hostingView.frame = contentRect
        hostingView.autoresizingMask = [.width, .height]
        contentView = hostingView
    }

    // MARK: - Key/Main

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

    // MARK: - Close Override

    /// Hide instead of closing so the SwiftUI state (text drafts, chat history) survives toggles.
    override func close() {
        orderOut(nil)
    }

    // MARK: - Escape Key

    /// ESC hides the panel.
    override func cancelOperation(_ sender: Any?) {
        close()
    }
}

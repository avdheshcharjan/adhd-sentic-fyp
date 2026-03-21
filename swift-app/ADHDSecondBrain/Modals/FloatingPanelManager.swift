import AppKit
import Observation

// MARK: - FloatingPanelManager

/// Manages the lifecycle of the Brain Dump and Vent floating panels.
///
/// Panels are created lazily on first toggle and reused thereafter.
/// ViewModels are kept as properties so state persists across hide/show cycles.
@MainActor
@Observable
final class FloatingPanelManager {

    // MARK: - ViewModels (persisted across toggles)

    let brainDumpViewModel = BrainDumpViewModel()
    let ventViewModel = VentViewModel()

    // MARK: - Private State

    private var brainDumpPanel: FloatingPanel<BrainDumpView>?
    private var ventPanel: FloatingPanel<VentView>?
    private var brainDumpMoveObserver: NSObjectProtocol?
    private var ventMoveObserver: NSObjectProtocol?

    private let brainDumpSize = CGSize(width: 520, height: 340)
    private let ventSize = CGSize(width: 440, height: 560)

    private let brainDumpPositionKey = "brainDumpPanelPosition"
    private let ventPositionKey = "ventPanelPosition"

    // MARK: - Toggle

    func toggleBrainDump() {
        if let panel = brainDumpPanel {
            if panel.isVisible {
                panel.close()
            } else {
                showPanel(panel, sizeKey: brainDumpPositionKey, size: brainDumpSize)
            }
            return
        }

        let panel = FloatingPanel(
            contentRect: NSRect(origin: .zero, size: brainDumpSize),
            content: BrainDumpView(
                viewModel: brainDumpViewModel,
                onSubmit: { [weak self] in
                    self?.brainDumpPanel?.close()
                }
            )
        )
        brainDumpPanel = panel
        showPanel(panel, sizeKey: brainDumpPositionKey, size: brainDumpSize)
    }

    func toggleVentModal() {
        if let panel = ventPanel {
            if panel.isVisible {
                panel.close()
            } else {
                showPanel(panel, sizeKey: ventPositionKey, size: ventSize)
            }
            return
        }

        let panel = FloatingPanel(
            contentRect: NSRect(origin: .zero, size: ventSize),
            content: VentView(viewModel: ventViewModel)
        )
        ventPanel = panel
        showPanel(panel, sizeKey: ventPositionKey, size: ventSize)
    }

    // MARK: - Positioning

    private func showPanel(_ panel: NSPanel, sizeKey: String, size: CGSize) {
        let origin = restoredOrigin(key: sizeKey, size: size)
        panel.setFrameOrigin(origin)
        panel.makeKeyAndOrderFront(nil)

        // Remove any previous observer to prevent leaks
        let existingObserver = (panel === brainDumpPanel) ? brainDumpMoveObserver : ventMoveObserver
        if let existingObserver {
            NotificationCenter.default.removeObserver(existingObserver)
        }

        // Persist position after every move via notification
        let observer = NotificationCenter.default.addObserver(
            forName: NSWindow.didMoveNotification,
            object: panel,
            queue: .main
        ) { [weak panel] _ in
            guard let panel else { return }
            let savedPoint = panel.frame.origin
            UserDefaults.standard.set(
                NSStringFromPoint(savedPoint),
                forKey: sizeKey
            )
        }

        if panel === brainDumpPanel {
            brainDumpMoveObserver = observer
        } else {
            ventMoveObserver = observer
        }
    }

    private func restoredOrigin(key: String, size: CGSize) -> NSPoint {
        if let saved = UserDefaults.standard.string(forKey: key) {
            let point = NSPointFromString(saved)
            // Validate the point is on screen
            if NSScreen.screens.contains(where: { NSMouseInRect(point, $0.visibleFrame, false) }) {
                return point
            }
        }
        return centeredOrigin(for: size)
    }

    private func centeredOrigin(for size: CGSize) -> NSPoint {
        guard let screen = NSScreen.main else {
            return NSPoint(x: 100, y: 100)
        }
        let frame = screen.visibleFrame
        return NSPoint(
            x: frame.midX - size.width / 2,
            y: frame.midY - size.height / 2
        )
    }
}

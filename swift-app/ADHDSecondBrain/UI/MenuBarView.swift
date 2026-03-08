import SwiftUI

/// Menu bar dropdown showing current focus state and quick actions.
struct MenuBarView: View {
    @ObservedObject var coordinator: MonitorCoordinator

    @State private var backendHealthy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Text("🧠 ADHD Second Brain")
                    .font(.headline)
                Spacer()
                Circle()
                    .fill(backendHealthy ? .green : .red)
                    .frame(width: 8, height: 8)
            }

            Divider()

            // Current State
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(coordinator.latestMetrics.stateEmoji)
                    Text(coordinator.latestMetrics.behavioralState.capitalized)
                        .font(.title3.bold())
                }

                HStack(spacing: 16) {
                    MetricPill(
                        label: "Focus",
                        value: "\(Int(coordinator.latestMetrics.focusScore))%"
                    )
                    MetricPill(
                        label: "Switches",
                        value: "\(Int(coordinator.latestMetrics.contextSwitchRate5min))"
                    )
                    MetricPill(
                        label: "Streak",
                        value: "\(Int(coordinator.latestMetrics.currentStreakMinutes))m"
                    )
                }

                if coordinator.latestCategory != "unknown" {
                    Text("Current: \(coordinator.latestCategory)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Divider()

            // Quick Actions
            Button {
                coordinator.toggleMonitoring()
            } label: {
                Label(
                    coordinator.isMonitoring ? "Pause Monitoring" : "Resume Monitoring",
                    systemImage: coordinator.isMonitoring ? "pause.circle" : "play.circle"
                )
            }

            Button {
                NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
            } label: {
                Label("Settings & Permissions", systemImage: "gear")
            }

            Divider()

            Button {
                NSApplication.shared.terminate(nil)
            } label: {
                Label("Quit", systemImage: "power")
            }
            .keyboardShortcut("q")
        }
        .padding()
        .frame(width: 280)
        .task {
            backendHealthy = await BackendClient().healthCheck()
        }
    }
}

/// Small pill showing a metric label + value.
struct MetricPill: View {
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.system(.body, design: .rounded).bold())
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(minWidth: 50)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

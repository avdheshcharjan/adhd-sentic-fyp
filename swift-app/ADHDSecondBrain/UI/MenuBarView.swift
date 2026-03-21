import SwiftUI

/// Menu bar dropdown showing current focus state and quick actions.
/// Layout and colours match the Paper canvas exactly.
struct MenuBarView: View {
    @ObservedObject var coordinator: MonitorCoordinator

    @Environment(\.openSettings) private var openSettings
    @Environment(\.openWindow) private var openWindow
    @State private var backendHealthy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            headerSection
            statsSection
            actionsSection
        }
        .frame(width: 280)
        .background(ADHDColors.Background.secondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(ADHDColors.Window.borderSubtle, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.5), radius: 48, x: 0, y: 0)
        .task {
            backendHealthy = await BackendClient().healthCheck()
            if !Permissions.hasAccessibility {
                openSettings()
            }
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(backendHealthy ? ADHDColors.Accent.successBright : ADHDColors.Accent.alert)
                .frame(width: 8, height: 8)

            Text("ADHD Second Brain")
                .font(.custom("Lexend-SemiBold", size: 14))
                .foregroundStyle(ADHDColors.Text.primary)

            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.top, 16)
        .padding(.bottom, 12)
    }

    // MARK: - Stats

    private var statsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(coordinator.latestMetrics.behavioralState.capitalized)
                .font(.custom("Lexend-Medium", size: 13))
                .foregroundStyle(ADHDColors.Accent.focusLight)

            HStack(spacing: 16) {
                MetricPill(
                    value: "\(Int(coordinator.latestMetrics.focusScore))%",
                    label: "Focus"
                )
                MetricPill(
                    value: "\(Int(coordinator.latestMetrics.contextSwitchRate5min))",
                    label: "Switches"
                )
                MetricPill(
                    value: "\(Int(coordinator.latestMetrics.currentStreakMinutes))m",
                    label: "Streak"
                )
            }

            if coordinator.latestCategory != "unknown" {
                Text("Current: \(coordinator.latestCategory)")
                    .font(.custom("Lexend-Regular", size: 11))
                    .foregroundStyle(ADHDColors.Text.tertiary)
            }
        }
        .padding(.horizontal, 18)
        .padding(.bottom, 14)
    }

    // MARK: - Actions

    private var actionsSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            actionButton(
                label: coordinator.isMonitoring ? "Pause Monitoring" : "Resume Monitoring",
                color: ADHDColors.Text.secondary
            ) {
                coordinator.toggleMonitoring()
            }

            actionButton(label: "Open Dashboard", color: ADHDColors.Text.secondary) {
                openWindow(id: "dashboard")
            }

            SettingsLink {
                actionRow(label: "Settings", color: ADHDColors.Text.secondary)
            }

            actionButton(label: "Quit", color: ADHDColors.Text.tertiary) {
                NSApplication.shared.terminate(nil)
            }
        }
        .padding(.vertical, 6)
        .background(ADHDColors.Background.elevated)
    }

    // MARK: - Action Helpers

    @ViewBuilder
    private func actionButton(
        label: String,
        color: Color,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            actionRow(label: label, color: color)
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func actionRow(label: String, color: Color) -> some View {
        Text(label)
            .font(.custom("Lexend-Regular", size: 13))
            .foregroundStyle(color)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 18)
            .padding(.vertical, 8)
            .contentShape(Rectangle())
    }
}

// MARK: - MetricPill

/// Vertical layout: large value on top, small label below. No background material.
struct MetricPill: View {
    let value: String
    let label: String

    var body: some View {
        VStack(alignment: .center, spacing: 2) {
            Text(value)
                .font(Font.custom("Lexend-Bold", size: 20).monospacedDigit())
                .foregroundStyle(ADHDColors.Text.primary)

            Text(label)
                .font(.custom("Lexend-Regular", size: 10))
                .foregroundStyle(ADHDColors.Text.tertiary)
        }
    }
}

import SwiftUI

// MARK: - Settings Tab Enum

enum SettingsTab: String, CaseIterable, Identifiable {
    case general      = "General"
    case permissions  = "Permissions"
    case focusSessions = "Focus Sessions"
    case whoop        = "Whoop"
    case notifications = "Notifications"
    case about        = "About"

    var id: String { rawValue }
}

// MARK: - Root Settings View

/// Two-panel settings window matching Paper canvas design.
/// 680px wide, minimum 440px tall.
/// Left sidebar (180px) + right content area.
struct SettingsView: View {

    @State private var selectedTab: SettingsTab = .general

    var body: some View {
        HStack(spacing: 0) {
            SettingsSidebar(selectedTab: $selectedTab)
                .frame(width: 180)

            Divider()
                .overlay(Color.white.opacity(0.06))

            SettingsContentArea(selectedTab: selectedTab)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .frame(width: 680, height: 440)
        .background(ADHDColors.Background.primary)
    }
}

// MARK: - Left Sidebar

private struct SettingsSidebar: View {
    @Binding var selectedTab: SettingsTab

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            ForEach(SettingsTab.allCases) { tab in
                SidebarNavItem(
                    title: tab.rawValue,
                    isSelected: selectedTab == tab
                ) {
                    selectedTab = tab
                }
            }
            Spacer()
        }
        .padding(12)
        .frame(maxHeight: .infinity)
        .background(ADHDColors.Background.elevated)
    }
}

// MARK: - Sidebar Nav Item

private struct SidebarNavItem: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(
                    isSelected
                        ? Font.custom("Lexend-Medium", size: 13)
                        : Font.custom("Lexend-Regular", size: 13)
                )
                .foregroundColor(
                    isSelected
                        ? ADHDColors.Accent.focusLight
                        : ADHDColors.Text.secondary
                )
                .frame(width: 156, alignment: .leading)
                .padding(.vertical, 8)
                .padding(.horizontal, 12)
                .background(
                    isSelected
                        ? ADHDColors.Accent.focusLight.opacity(0.08)
                        : Color.clear
                )
                .cornerRadius(10)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Right Content Area (tab router)

private struct SettingsContentArea: View {
    let selectedTab: SettingsTab

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            switch selectedTab {
            case .general:
                GeneralSettingsPage()
            case .permissions:
                PlaceholderSettingsPage(title: "Permissions")
            case .focusSessions:
                PlaceholderSettingsPage(title: "Focus Sessions")
            case .whoop:
                PlaceholderSettingsPage(title: "Whoop")
            case .notifications:
                PlaceholderSettingsPage(title: "Notifications")
            case .about:
                PlaceholderSettingsPage(title: "About")
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - General Settings Page

private struct GeneralSettingsPage: View {

    @AppStorage("launchAtLogin")     private var launchAtLogin: Bool   = true
    @AppStorage("notchWidget")       private var notchWidget: Bool      = true
    @AppStorage("reducedMotion")     private var reducedMotion: Bool    = false
    @AppStorage("defaultFocusBlock") private var defaultFocusBlock: Int = 45
    @AppStorage("backendURL")        private var backendURL: String     = "localhost:8420"

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("General")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 24) {
                SettingsToggleRow(
                    label: "Launch at login",
                    description: "Start monitoring when you log in",
                    isOn: $launchAtLogin
                )

                SettingsToggleRow(
                    label: "Notch widget",
                    description: "Show the Dynamic Island overlay",
                    isOn: $notchWidget
                )

                SettingsToggleRow(
                    label: "Reduced motion",
                    description: "Minimize animations and transitions",
                    isOn: $reducedMotion
                )

                SettingsValuePillRow(
                    label: "Default focus block",
                    description: "Duration before a break is suggested",
                    valueText: "\(defaultFocusBlock) min"
                )

                SettingsURLRow(
                    label: "Backend URL",
                    description: "API endpoint for the Python backend",
                    value: $backendURL
                )

                SettingsGoogleCalendarRow()
            }
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Reusable Settings Row Components

/// A row with a label/description on the left and a toggle on the right.
private struct SettingsToggleRow: View {
    let label: String
    let description: String
    @Binding var isOn: Bool

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            SettingsToggle(isOn: $isOn)
        }
    }
}

/// A row with a label/description on the left and a static value pill on the right.
private struct SettingsValuePillRow: View {
    let label: String
    let description: String
    let valueText: String

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            SettingsValuePill(text: valueText)
        }
    }
}

/// A row for the backend URL — shows the URL in a pill with muted styling.
private struct SettingsURLRow: View {
    let label: String
    let description: String
    @Binding var value: String

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            Text(value)
                .font(Font.custom("Lexend-Regular", size: 13))
                .foregroundColor(ADHDColors.Text.secondary)
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background(ADHDColors.Background.secondary)
                .cornerRadius(10)
        }
    }
}

/// Left-side label + description stack used in all setting rows.
private struct SettingsRowLabel: View {
    let label: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(Font.custom("Lexend-Medium", size: 14))
                .foregroundColor(ADHDColors.Text.primary)
            Text(description)
                .font(Font.custom("Lexend-Regular", size: 12))
                .foregroundColor(ADHDColors.Text.tertiary)
        }
    }
}

/// 44x24 pill toggle. on = green (0x28C840), off = muted (0x47474D).
private struct SettingsToggle: View {
    @Binding var isOn: Bool

    private let width: CGFloat  = 44
    private let height: CGFloat = 24
    private let knobSize: CGFloat = 20

    var body: some View {
        ZStack {
            Capsule()
                .fill(isOn ? ADHDColors.Accent.successBright : ADHDColors.Text.muted)
                .frame(width: width, height: height)

            Circle()
                .fill(Color.white)
                .frame(width: knobSize, height: knobSize)
                .offset(x: isOn ? (width / 2 - knobSize / 2 - 2) : -(width / 2 - knobSize / 2 - 2))
                .animation(.spring(response: 0.25, dampingFraction: 0.75), value: isOn)
        }
        .frame(width: width, height: height)
        .contentShape(Rectangle())
        .onTapGesture { isOn.toggle() }
    }
}

/// Static value pill — dark background, primary text, tabular digits.
private struct SettingsValuePill: View {
    let text: String

    var body: some View {
        Text(text)
            .font(
                Font.custom("Lexend-Medium", size: 14)
                    .monospacedDigit()
            )
            .foregroundColor(ADHDColors.Text.primary)
            .padding(.vertical, 6)
            .padding(.horizontal, 14)
            .background(ADHDColors.Background.secondary)
            .cornerRadius(10)
    }
}

// MARK: - Google Calendar Connection Row

private struct SettingsGoogleCalendarRow: View {
    @State private var isConnected = false
    @State private var isChecking = false

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(
                label: "Google Calendar",
                description: isConnected
                    ? "Connected — events sync every 30s"
                    : "Link your calendar to see upcoming events"
            )
            Spacer()

            if isConnected {
                HStack(spacing: 6) {
                    Circle()
                        .fill(ADHDColors.Accent.success)
                        .frame(width: 8, height: 8)
                    Text("Connected")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.success)
                }
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background(ADHDColors.Accent.success.opacity(0.1))
                .cornerRadius(10)
            } else {
                Button {
                    guard let url = URL(string: "http://localhost:8420/api/auth/google") else { return }
                    NSWorkspace.shared.open(url)
                } label: {
                    Text("Connect")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.focusLight)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Accent.focusLight.opacity(0.1))
                        .cornerRadius(10)
                }
                .buttonStyle(.plain)
            }
        }
        .task {
            await checkStatus()
        }
    }

    private func checkStatus() async {
        guard !isChecking else { return }
        isChecking = true
        defer { isChecking = false }

        guard let url = URL(string: "http://localhost:8420/api/auth/google/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Status: Decodable { let connected: Bool }
            if let status = try? JSONDecoder().decode(Status.self, from: data) {
                isConnected = status.connected
            }
        } catch {
            // Backend not reachable
        }
    }
}

// MARK: - Placeholder for unimplemented tabs

private struct PlaceholderSettingsPage: View {
    let title: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

import SwiftUI
import KeyboardShortcuts

// MARK: - Modal Settings Page

/// Settings page for Brain Dump and Vent keyboard shortcuts.
/// Matches the General settings page layout pattern.
struct ModalSettingsView: View {

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Shortcuts")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 24) {
                ShortcutRecorderRow(
                    label: "Brain Dump",
                    description: "Opens a quick capture window for thoughts",
                    shortcutName: .brainDump
                )

                ShortcutRecorderRow(
                    label: "Vent Space",
                    description: "Opens a private space to process emotions",
                    shortcutName: .ventModal
                )
            }

            Spacer().frame(height: 20)

            Text("Click a shortcut to record a new key combination")
                .font(Font.custom("Lexend-Regular", size: 11))
                .foregroundColor(ADHDColors.Text.muted)
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Shortcut Recorder Row

/// A row with label/description on the left and a KeyboardShortcuts.Recorder on the right.
private struct ShortcutRecorderRow: View {
    let label: String
    let description: String
    let shortcutName: KeyboardShortcuts.Name

    var body: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(Font.custom("Lexend-Medium", size: 14))
                    .foregroundColor(ADHDColors.Text.primary)
                Text(description)
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.tertiary)
            }
            Spacer()
            KeyboardShortcuts.Recorder("", name: shortcutName)
        }
    }
}

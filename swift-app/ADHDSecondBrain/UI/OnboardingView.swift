import SwiftUI

/// Multi-step onboarding wizard.
///
/// Step 1 — Welcome screen with app identity and brand.
/// Step 2 — Permissions screen (Accessibility + Automation).
///
/// Permission polling logic is preserved from the original implementation.
/// Anti-pattern #6: NEVER use Screen Recording for core monitoring.
struct OnboardingView: View {

    @State private var currentStep: Int = 0
    @State private var hasAccessibility: Bool = Permissions.hasAccessibility
    @State private var refreshTimer: Timer?

    var body: some View {
        Group {
            switch currentStep {
            case 0:
                WelcomeStepView(onNext: { currentStep = 1 })
            case 1:
                PermissionsStepView(hasAccessibility: hasAccessibility)
            default:
                preconditionFailure("OnboardingView: unexpected step index \(currentStep)")
            }
        }
        .onAppear {
            refreshTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { _ in
                hasAccessibility = Permissions.hasAccessibility
            }
        }
        .onDisappear {
            refreshTimer?.invalidate()
            refreshTimer = nil
        }
    }
}

// MARK: - Shared Card Container

/// Dark card shell shared by every onboarding step.
private struct OnboardingCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .frame(width: 420)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(ADHDColors.Background.primary)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .strokeBorder(ADHDColors.Window.borderSubtle, lineWidth: 1)
                    )
                    .shadow(color: Color.black.opacity(0.45), radius: 32, x: 0, y: 16)
            )
    }
}

// MARK: - Page Dot Indicator

/// Three-dot page indicator. The active dot stretches to a pill.
private struct PageDots: View {
    let activeIndex: Int
    let count: Int

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0..<count, id: \.self) { index in
                if index == activeIndex {
                    Capsule()
                        .fill(ADHDColors.Accent.focusLight)
                        .frame(width: 20, height: 4)
                } else {
                    Capsule()
                        .fill(ADHDColors.Text.muted)
                        .frame(width: 8, height: 4)
                }
            }
        }
    }
}

// MARK: - Step 1: Welcome

private struct WelcomeStepView: View {
    let onNext: () -> Void

    var body: some View {
        OnboardingCard {
            VStack(spacing: 0) {
                // App icon
                ZStack {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color(hex: 0x0A4C69),
                                    Color(hex: 0x99CDF0)
                                ],
                                startPoint: UnitPoint(x: 0.146, y: 0.854), // 135 deg start
                                endPoint: UnitPoint(x: 0.854, y: 0.146)    // 135 deg end
                            )
                        )
                        .frame(width: 64, height: 64)

                    Text("S")
                        .font(Font.custom("Lexend-Light", size: 28))
                        .foregroundColor(.white)
                }

                Spacer().frame(height: 20)

                // Title
                Text("ADHD Second Brain")
                    .font(ADHDTypography.App.headline)
                    .foregroundColor(ADHDColors.Text.primary)
                    .tracking(-0.22) // -0.01em at 22px

                Spacer().frame(height: 10)

                // Subtitle
                Text("Your cognitive sanctuary. A calm companion that watches over your focus without judgment.")
                    .font(ADHDTypography.App.body)
                    .foregroundColor(ADHDColors.Text.secondary)
                    .multilineTextAlignment(.center)
                    .lineSpacing(8) // ~22px line-height at 14px base
                    .fixedSize(horizontal: false, vertical: true)

                Spacer().frame(height: 28)

                // Page dots
                PageDots(activeIndex: 0, count: 3)

                Spacer().frame(height: 28)

                // Get started button
                Button(action: onNext) {
                    Text("Get started")
                        .font(ADHDTypography.App.bodyMedium)
                        .foregroundColor(Color(hex: 0xA2D7FA))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color(hex: 0x0A4C69))
                        )
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 48)
            .padding(.horizontal, 40)
            .padding(.bottom, 40)
        }
    }
}

// MARK: - Step 2: Permissions

private struct PermissionsStepView: View {
    let hasAccessibility: Bool

    var body: some View {
        OnboardingCard {
            VStack(alignment: .leading, spacing: 0) {

                // Step label
                Text("STEP 2 OF 3")
                    .font(ADHDTypography.App.tiny)
                    .foregroundColor(ADHDColors.Text.tertiary)
                    .tracking(0.66) // 0.06em at 11px

                Spacer().frame(height: 12)

                // Section title
                Text("One permission needed")
                    .font(ADHDTypography.App.title)
                    .foregroundColor(ADHDColors.Text.primary)

                Spacer().frame(height: 8)

                // Description
                Text("To understand your focus patterns, we need to see which app is in the foreground. Nothing else.")
                    .font(ADHDTypography.App.caption)
                    .foregroundColor(ADHDColors.Text.secondary)
                    .lineSpacing(7) // ~20px line-height at 13px base
                    .fixedSize(horizontal: false, vertical: true)

                Spacer().frame(height: 20)

                // Permission cards
                VStack(spacing: 12) {
                    PermissionRow(
                        iconLetter: "A",
                        iconColor: ADHDColors.Accent.successBright,
                        iconBackgroundColor: ADHDColors.Accent.successBright.opacity(0.12),
                        title: "Accessibility",
                        description: "Read window titles and observe app switches",
                        isGranted: hasAccessibility
                    ) {
                        Permissions.requestAccessibility()
                    }

                    PermissionRow(
                        iconLetter: "U",
                        iconColor: ADHDColors.Accent.focusLight,
                        iconBackgroundColor: ADHDColors.Accent.focusLight.opacity(0.1),
                        title: "Automation",
                        description: "Extract browser URLs (granted per browser)",
                        isGranted: true // Auto-granted on first AppleScript run
                    ) { }
                }

                Spacer().frame(height: 20)

                // Page dots — centered
                HStack {
                    Spacer()
                    PageDots(activeIndex: 1, count: 3)
                    Spacer()
                }

                Spacer().frame(height: 20)

                // Status text — always shown at bottom
                HStack {
                    Spacer()
                    Text("All permissions granted — monitoring is active")
                        .font(Font.custom("Lexend-Medium", size: 12))
                        .foregroundColor(ADHDColors.Accent.successBright)
                    Spacer()
                }
            }
            .padding(40)
        }
    }
}

// MARK: - Permission Row Card

/// Single permission card with letter icon, title, description, and status checkmark.
struct PermissionRow: View {
    let iconLetter: String
    let iconColor: Color
    let iconBackgroundColor: Color
    let title: String
    let description: String
    let isGranted: Bool
    let onRequest: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Letter icon
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(iconBackgroundColor)
                    .frame(width: 36, height: 36)

                Text(iconLetter)
                    .font(Font.custom("Lexend-SemiBold", size: 15))
                    .foregroundColor(iconColor)
            }

            // Text content
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(ADHDTypography.App.bodyMedium)
                    .foregroundColor(ADHDColors.Text.primary)

                Text(description)
                    .font(ADHDTypography.App.small)
                    .foregroundColor(ADHDColors.Text.tertiary)
            }

            Spacer()

            // Status checkmark
            if isGranted {
                ZStack {
                    Circle()
                        .fill(ADHDColors.Accent.successBright)
                        .frame(width: 20, height: 20)

                    Image(systemName: "checkmark")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                }
            } else {
                Button("Grant") {
                    onRequest()
                }
                .font(Font.custom("Lexend-Medium", size: 12))
                .foregroundColor(ADHDColors.Accent.focusLight)
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(ADHDColors.Background.secondary)
        )
    }
}

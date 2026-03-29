import SwiftUI

@MainActor @Observable
final class TaskCreationViewModel {
    var taskName: String = ""
    var selectedDuration: FocusDuration = .twentyFive

    var canSubmit: Bool {
        !taskName.trimmingCharacters(in: .whitespaces).isEmpty
    }

    func reset() {
        taskName = ""
        selectedDuration = .twentyFive
    }
}

enum FocusDuration: Int, CaseIterable, Identifiable {
    case fifteen = 15
    case twentyFive = 25
    case fortyFive = 45
    case sixty = 60
    case onetwenty = 120

    var id: Int { rawValue }

    var label: String {
        switch self {
        case .fifteen: "15m"
        case .twentyFive: "25m"
        case .fortyFive: "45m"
        case .sixty: "1hr"
        case .onetwenty: "2hr"
        }
    }

    var seconds: TimeInterval {
        TimeInterval(rawValue * 60)
    }
}

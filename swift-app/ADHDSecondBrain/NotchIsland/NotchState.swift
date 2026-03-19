import Foundation

enum NotchState: Equatable {
    case dormant
    case ambient
    case glanceable
    case expanded
    case alert(InterventionTier)

    /// Numeric rank for determining open vs close direction.
    var ordinal: Int {
        switch self {
        case .dormant: 0
        case .ambient: 1
        case .glanceable: 2
        case .expanded: 3
        case .alert: 3
        }
    }
}

enum InterventionTier: Int, Comparable, Equatable {
    case passive = 0
    case gentle = 1
    case timeSensitive = 2
    case actionRequired = 3
    case critical = 4

    static func < (lhs: InterventionTier, rhs: InterventionTier) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}

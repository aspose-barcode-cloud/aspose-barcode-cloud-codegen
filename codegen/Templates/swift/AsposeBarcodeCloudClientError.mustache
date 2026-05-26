import Foundation

public enum AsposeBarcodeCloudClientError: Error, CustomStringConvertible, @unchecked Sendable {
    case missingCredentials
    case invalidTokenURL(String)
    case invalidTokenResponse
    case tokenRequestFailed(statusCode: Int, body: String?)
    case transportError(Error)

    public var description: String {
        switch self {
        case .missingCredentials:
            return "Access token or clientId/clientSecret are required"
        case let .invalidTokenURL(url):
            return "Invalid token URL: \(url)"
        case .invalidTokenResponse:
            return "Token response does not contain access_token"
        case let .tokenRequestFailed(statusCode, body):
            if let body = body, !body.isEmpty {
                return "Token request failed with status \(statusCode): \(body)"
            }
            return "Token request failed with status \(statusCode)"
        case let .transportError(error):
            return error.localizedDescription
        }
    }
}

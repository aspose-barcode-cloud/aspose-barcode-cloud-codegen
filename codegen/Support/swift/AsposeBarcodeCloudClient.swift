import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public enum AsposeBarcodeCloudClientError: Error, CustomStringConvertible {
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

public final class AsposeBarcodeCloudConfiguration {
    public static let defaultHost = "https://api.aspose.cloud/v4.0"
    public static let defaultTokenURL = "https://id.aspose.cloud/connect/token"
    public static let defaultSdkName = "swift sdk"
    public static let defaultSdkVersion = "26.4.0"

    public var host: String
    public var tokenURL: String
    public var accessToken: String?
    public var clientId: String?
    public var clientSecret: String?
    public var sdkName: String
    public var sdkVersion: String
    public var timeoutInterval: TimeInterval

    public init(
        accessToken: String? = nil,
        clientId: String? = nil,
        clientSecret: String? = nil,
        host: String = AsposeBarcodeCloudConfiguration.defaultHost,
        tokenURL: String = AsposeBarcodeCloudConfiguration.defaultTokenURL,
        sdkName: String = AsposeBarcodeCloudConfiguration.defaultSdkName,
        sdkVersion: String = AsposeBarcodeCloudConfiguration.defaultSdkVersion,
        timeoutInterval: TimeInterval = 300
    ) {
        self.accessToken = accessToken
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.host = host
        self.tokenURL = tokenURL
        self.sdkName = sdkName
        self.sdkVersion = sdkVersion
        self.timeoutInterval = timeoutInterval
    }

    public func makeTokenRequest() throws -> URLRequest {
        guard let clientId = clientId, !clientId.isEmpty,
              let clientSecret = clientSecret, !clientSecret.isEmpty else {
            throw AsposeBarcodeCloudClientError.missingCredentials
        }

        guard let url = URL(string: tokenURL) else {
            throw AsposeBarcodeCloudClientError.invalidTokenURL(tokenURL)
        }

        var components = URLComponents()
        components.queryItems = [
            URLQueryItem(name: "grant_type", value: "client_credentials"),
            URLQueryItem(name: "client_id", value: clientId),
            URLQueryItem(name: "client_secret", value: clientSecret),
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = timeoutInterval
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = components.percentEncodedQuery?.data(using: .utf8)
        return request
    }
}

public typealias AsposeBarcodeCloudTokenFetcher = (
    AsposeBarcodeCloudConfiguration,
    @escaping (Result<String, AsposeBarcodeCloudClientError>) -> Void
) -> Void

public final class AsposeBarcodeCloudClient {
    public let configuration: AsposeBarcodeCloudConfiguration
    private let tokenFetcher: AsposeBarcodeCloudTokenFetcher

    public init(
        configuration: AsposeBarcodeCloudConfiguration,
        tokenFetcher: AsposeBarcodeCloudTokenFetcher? = nil
    ) {
        self.configuration = configuration
        self.tokenFetcher = tokenFetcher ?? AsposeBarcodeCloudClient.defaultTokenFetcher
    }

    public convenience init(
        clientId: String,
        clientSecret: String,
        host: String = AsposeBarcodeCloudConfiguration.defaultHost,
        tokenURL: String = AsposeBarcodeCloudConfiguration.defaultTokenURL
    ) {
        self.init(configuration: AsposeBarcodeCloudConfiguration(
            clientId: clientId,
            clientSecret: clientSecret,
            host: host,
            tokenURL: tokenURL
        ))
    }

    public convenience init(
        accessToken: String,
        host: String = AsposeBarcodeCloudConfiguration.defaultHost
    ) {
        self.init(configuration: AsposeBarcodeCloudConfiguration(
            accessToken: accessToken,
            host: host
        ))
    }

    public func apply() {
        AsposeBarcodeCloudAPI.basePath = configuration.host
        AsposeBarcodeCloudAPI.customHeaders["x-aspose-client"] = configuration.sdkName
        AsposeBarcodeCloudAPI.customHeaders["x-aspose-client-version"] = configuration.sdkVersion

        if let accessToken = configuration.accessToken, !accessToken.isEmpty {
            AsposeBarcodeCloudAPI.customHeaders["Authorization"] = "Bearer \(accessToken)"
        } else {
            AsposeBarcodeCloudAPI.customHeaders.removeValue(forKey: "Authorization")
        }
    }

    public func authorize(completion: @escaping (Result<String, AsposeBarcodeCloudClientError>) -> Void) {
        if let accessToken = configuration.accessToken, !accessToken.isEmpty {
            apply()
            completion(.success(accessToken))
            return
        }

        tokenFetcher(configuration) { result in
            switch result {
            case let .success(accessToken):
                self.configuration.accessToken = accessToken
                self.apply()
                completion(.success(accessToken))
            case let .failure(error):
                completion(.failure(error))
            }
        }
    }

    @discardableResult
    public func authorize() throws -> String {
        let semaphore = DispatchSemaphore(value: 0)
        var tokenResult: Result<String, AsposeBarcodeCloudClientError>?

        authorize { result in
            tokenResult = result
            semaphore.signal()
        }

        semaphore.wait()

        switch tokenResult {
        case let .success(accessToken):
            return accessToken
        case let .failure(error):
            throw error
        case .none:
            throw AsposeBarcodeCloudClientError.invalidTokenResponse
        }
    }

    public static func resetGlobalConfiguration() {
        AsposeBarcodeCloudAPI.basePath = AsposeBarcodeCloudConfiguration.defaultHost
        AsposeBarcodeCloudAPI.customHeaders.removeAll()
    }

    private struct TokenResponse: Decodable {
        let accessToken: String?

        enum CodingKeys: String, CodingKey {
            case accessToken = "access_token"
        }
    }

    private static func defaultTokenFetcher(
        configuration: AsposeBarcodeCloudConfiguration,
        completion: @escaping (Result<String, AsposeBarcodeCloudClientError>) -> Void
    ) {
        let request: URLRequest
        do {
            request = try configuration.makeTokenRequest()
        } catch let error as AsposeBarcodeCloudClientError {
            completion(.failure(error))
            return
        } catch {
            completion(.failure(.transportError(error)))
            return
        }

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(.transportError(error)))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(.invalidTokenResponse))
                return
            }

            guard 200..<300 ~= httpResponse.statusCode else {
                let body = data.flatMap { String(data: $0, encoding: .utf8) }
                completion(.failure(.tokenRequestFailed(statusCode: httpResponse.statusCode, body: body)))
                return
            }

            guard let data = data,
                  let tokenResponse = try? JSONDecoder().decode(TokenResponse.self, from: data),
                  let accessToken = tokenResponse.accessToken,
                  !accessToken.isEmpty else {
                completion(.failure(.invalidTokenResponse))
                return
            }

            completion(.success(accessToken))
        }.resume()
    }
}

import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public typealias AsposeBarcodeCloudTokenFetcher = @Sendable (
    AsposeBarcodeCloudConfiguration,
    @escaping @Sendable (Result<String, AsposeBarcodeCloudClientError>) -> Void
) -> Void

public final class AsposeBarcodeCloudClient: @unchecked Sendable {
    public let configuration: AsposeBarcodeCloudConfiguration
    public let apiConfiguration: AsposeBarcodeCloudAPIConfiguration
    private let authInterceptor: BarcodeAuthInterceptor

    public init(
        configuration: AsposeBarcodeCloudConfiguration,
        tokenFetcher: AsposeBarcodeCloudTokenFetcher? = nil
    ) {
        self.configuration = configuration
        let fetcher = tokenFetcher ?? AsposeBarcodeCloudClient.defaultTokenFetcher

        let apiConfig = AsposeBarcodeCloudAPIConfiguration(
            basePath: configuration.host,
            customHeaders: [
                "x-aspose-client": configuration.sdkName,
                "x-aspose-client-version": configuration.sdkVersion,
            ]
        )
        let interceptor = BarcodeAuthInterceptor(
            configuration: configuration,
            tokenFetcher: fetcher
        )
        apiConfig.interceptor = interceptor

        self.apiConfiguration = apiConfig
        self.authInterceptor = interceptor
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

    public func authorize(completion: @escaping @Sendable (Result<String, AsposeBarcodeCloudClientError>) -> Void) {
        authInterceptor.ensureToken(completion: completion)
    }

    @discardableResult
    public func authorize() async throws -> String {
        try await withCheckedThrowingContinuation { continuation in
            authorize { result in
                switch result {
                case let .success(token):
                    continuation.resume(returning: token)
                case let .failure(error):
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    private struct TokenResponse: Decodable {
        let accessToken: String?

        enum CodingKeys: String, CodingKey {
            case accessToken = "access_token"
        }
    }

    private static func defaultTokenFetcher(
        configuration: AsposeBarcodeCloudConfiguration,
        completion: @escaping @Sendable (Result<String, AsposeBarcodeCloudClientError>) -> Void
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

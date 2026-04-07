# Implementation Guide: Google Sign-In (Flutter)

This guide provides the necessary steps and code snippets to implement Google Sign-In in your Flutter application, integrating with the Starboy Global backend.

## 1. Project Setup

### Android Setup
1.  **Google Cloud Console**: Create a project and configure the OAuth consent screen.
2.  **Generate SHA-1**: Run `./gradlew signingReport` in the `android/` directory to get your SHA-1 fingerprint.
3.  **Firebase/Google Cloud**: Add an Android app with your package name and SHA-1.
4.  **`google-services.json`**: Download and place it in `android/app/`.

### iOS Setup
1.  **Google Cloud Console**: Add an iOS app and provide your Bundle ID.
2.  **`GoogleService-Info.plist`**: Download and place it in the `Runner/` directory via Xcode.
3.  **URL Schemes**: Add the `REVERSED_CLIENT_ID` from the plist as a URL scheme.

---

## 2. Flutter Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  google_sign_in: ^6.2.1
  http: ^1.2.0
```

---

## 3. Implementation Code

### Core Authentication Logic

```dart
import 'package:google_sign_in/google_sign_in.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
    // serverClientId is required for some platforms to get idToken
    // serverClientId: 'YOUR_SERVER_CLIENT_ID.apps.googleusercontent.com', 
  );

  Future<void> signInWithGoogle() async {
    try {
      final GoogleSignInAccount? account = await _googleSignIn.signIn();
      
      if (account == null) return; // User cancelled

      final GoogleSignInAuthentication auth = await account.authentication;
      final String? idToken = auth.idToken;

      if (idToken != null) {
        // Send to your backend
        await _authenticateWithBackend(idToken);
      }
    } catch (error) {
      print('Google Sign-In Error: $error');
    }
  }

  Future<void> _authenticateWithBackend(String idToken) async {
    final response = await http.post(
      Uri.parse('https://api.starboyglobal.com.ng/api/account/google-auth/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'id_token': idToken}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      // Success: Save tokens
      String access = data['access'];
      bool isNewUser = data['is_new_user'];
      
      if (isNewUser) {
        // Navigate to Profile Completion / Phone Number Required screen
        // final googleData = data['google_data'];
      } else {
        // Navigate to Dashboard
      }
    } else if (response.statusCode == 400 && data['code'] == 'PHONE_NUMBER_REQUIRED') {
      // Navigate to Phone Verification Screen
      showPhoneInputScreen(idToken, data['google_data']);
    }
  }
}
```

---

## 4. Backend integration Details

- **Endpoint**: `/api/account/google-auth/`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "id_token": "EYJhbGciOiJSUzI1NiIsImt..."
  }
  ```
- **Responses**:
  - `200 OK`: Successful login. Returns `access`, `refresh`, and `is_new_user`.
  - `400 Bad Request`: If phone number is missing (new user registration flow). Return includes `google_data` for pre-filling.
  - `202 Accepted`: If 2FA is enabled on the account.

### Why use `idToken`?
We use `idToken` on the backend because it contains verified user identities (email, name, sub) that the backend can cryptographically verify using Google's public keys, ensuring the request is authentic.

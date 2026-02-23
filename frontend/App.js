import { useMemo, useState } from "react";
import { SafeAreaView, ScrollView, Text, TextInput, TouchableOpacity, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { analyze, getProfile, login, me, recommend, refresh, signup } from "./src/api";

const buttonStyle = {
  backgroundColor: "#194f3f",
  paddingVertical: 12,
  paddingHorizontal: 14,
  borderRadius: 10,
  marginTop: 10,
};

export default function App() {
  const [email, setEmail] = useState("tester@example.com");
  const [password, setPassword] = useState("Password123!");
  const [fullName, setFullName] = useState("Test User");
  const [token, setToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  const isAuthed = useMemo(() => token.length > 0 && userId.length > 0, [token, userId]);

  const handleSignup = async () => {
    try {
      setError("");
      await signup(email, password, fullName);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Signup failed");
    }
  };

  const handleLogin = async () => {
    try {
      setError("");
      const data = await login(email, password);
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUserId(data.user_id);
      setRole(data.role);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Login failed");
    }
  };

  const handleRefresh = async () => {
    try {
      setError("");
      const data = await refresh(refreshToken);
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setRole(data.role);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Refresh failed");
    }
  };

  const handleMe = async () => {
    try {
      setError("");
      const data = await me(token);
      setRole(data.role);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Me failed");
    }
  };

  const handleAnalyze = async () => {
    try {
      setError("");
      const data = await analyze(token);
      setAnalysis(data.profile);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Analyze failed");
    }
  };

  const handleRecommend = async () => {
    if (!analysis) {
      setError("Run analysis first");
      return;
    }
    try {
      setError("");
      const data = await recommend(token, analysis.skin_type, analysis.conditions);
      setRecommendations(data.products || []);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Recommend failed");
    }
  };

  const handleProfile = async () => {
    try {
      setError("");
      const data = await getProfile(token, userId);
      setProfile(data);
    } catch (err) {
      setError(err?.response?.data?.error?.message || "Profile fetch failed");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#f4f7f1" }}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 8 }}>
        <Text style={{ fontSize: 24, fontWeight: "700", color: "#12352b" }}>SkinCare AI</Text>

        <TextInput
          value={fullName}
          onChangeText={setFullName}
          placeholder="Full name"
          style={{ borderWidth: 1, borderColor: "#99a8a1", borderRadius: 8, padding: 10, backgroundColor: "white" }}
        />
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="Email"
          autoCapitalize="none"
          style={{ borderWidth: 1, borderColor: "#99a8a1", borderRadius: 8, padding: 10, backgroundColor: "white" }}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="Password"
          secureTextEntry
          style={{ borderWidth: 1, borderColor: "#99a8a1", borderRadius: 8, padding: 10, backgroundColor: "white" }}
        />

        <TouchableOpacity style={buttonStyle} onPress={handleSignup}>
          <Text style={{ color: "white", fontWeight: "600" }}>Signup</Text>
        </TouchableOpacity>

        <TouchableOpacity style={buttonStyle} onPress={handleLogin}>
          <Text style={{ color: "white", fontWeight: "600" }}>Login</Text>
        </TouchableOpacity>

        <TouchableOpacity style={buttonStyle} onPress={handleRefresh} disabled={!refreshToken}>
          <Text style={{ color: "white", fontWeight: "600" }}>Refresh Token</Text>
        </TouchableOpacity>

        <TouchableOpacity style={buttonStyle} onPress={handleMe} disabled={!isAuthed}>
          <Text style={{ color: "white", fontWeight: "600" }}>Who Am I</Text>
        </TouchableOpacity>

        <Text style={{ marginTop: 8, color: "#12352b" }}>Authenticated: {isAuthed ? "Yes" : "No"} | Role: {role || "-"}</Text>

        <TouchableOpacity style={buttonStyle} onPress={handleAnalyze} disabled={!isAuthed}>
          <Text style={{ color: "white", fontWeight: "600" }}>Analyze</Text>
        </TouchableOpacity>

        <TouchableOpacity style={buttonStyle} onPress={handleRecommend} disabled={!isAuthed}>
          <Text style={{ color: "white", fontWeight: "600" }}>Recommend</Text>
        </TouchableOpacity>

        <TouchableOpacity style={buttonStyle} onPress={handleProfile} disabled={!isAuthed}>
          <Text style={{ color: "white", fontWeight: "600" }}>Get Profile</Text>
        </TouchableOpacity>

        {analysis ? (
          <View style={{ marginTop: 10, padding: 10, backgroundColor: "#e9f1eb", borderRadius: 8 }}>
            <Text>Skin type: {analysis.skin_type}</Text>
            <Text>Conditions: {analysis.conditions.join(", ")}</Text>
            <Text>Confidence: {analysis.confidence}</Text>
          </View>
        ) : null}

        {recommendations.length > 0 ? (
          <View style={{ marginTop: 10, padding: 10, backgroundColor: "#eaf0f8", borderRadius: 8 }}>
            <Text style={{ fontWeight: "700", marginBottom: 6 }}>Recommendations</Text>
            {recommendations.map((item) => (
              <Text key={item.sku}>{item.name} ({item.score})</Text>
            ))}
          </View>
        ) : null}

        {profile ? (
          <View style={{ marginTop: 10, padding: 10, backgroundColor: "#f2ece2", borderRadius: 8 }}>
            <Text style={{ fontWeight: "700", marginBottom: 6 }}>Profile History: {profile.history.length}</Text>
            {profile.history.slice(0, 3).map((entry, idx) => (
              <Text key={`${entry.timestamp}-${idx}`}>
                {entry.skin_type} | {entry.conditions.join(", ")} | {entry.confidence}
              </Text>
            ))}
          </View>
        ) : null}

        {error ? <Text style={{ marginTop: 10, color: "#b00020" }}>{error}</Text> : null}
      </ScrollView>
      <StatusBar style="dark" />
    </SafeAreaView>
  );
}

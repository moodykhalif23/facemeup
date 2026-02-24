import { useState } from "react";
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from "react-native";
import { InputItem, Button, WhiteSpace, WingBlank, Toast } from '@ant-design/react-native';
import { login, signup } from "../api";

export default function AuthScreen({ navigation, onAuth }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password || (!isLogin && !fullName)) {
      Toast.fail("Please fill in all fields", 2);
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        const data = await login(email, password);
        onAuth(data);
        Toast.success("Login successful!", 1);
      } else {
        await signup(email, password, fullName);
        Toast.success("Account created! Please login.", 2);
        setIsLogin(true);
      }
    } catch (err) {
      Toast.fail(err?.response?.data?.error?.message || `${isLogin ? "Login" : "Signup"} failed`, 2);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.logo}>✨</Text>
            <Text style={styles.title}>SkinCare AI</Text>
            <Text style={styles.subtitle}>Your personalized skincare companion</Text>
          </View>

          <View style={styles.form}>
            <WingBlank size="lg">
              {!isLogin && (
                <>
                  <Text style={styles.label}>Full Name</Text>
                  <InputItem
                    value={fullName}
                    onChange={setFullName}
                    placeholder="Enter your full name"
                    clear
                    style={styles.input}
                  />
                  <WhiteSpace size="lg" />
                </>
              )}

              <Text style={styles.label}>Email</Text>
              <InputItem
                value={email}
                onChange={setEmail}
                placeholder="Enter your email"
                type="email-address"
                clear
                style={styles.input}
              />
              <WhiteSpace size="lg" />

              <Text style={styles.label}>Password</Text>
              <InputItem
                value={password}
                onChange={setPassword}
                placeholder="Enter your password"
                type="password"
                style={styles.input}
              />
              <WhiteSpace size="xl" />

              <Button
                type="primary"
                onPress={handleSubmit}
                loading={loading}
                disabled={loading}
                style={styles.button}
              >
                {isLogin ? "Login" : "Sign Up"}
              </Button>

              <WhiteSpace size="lg" />

              <Button
                type="ghost"
                onPress={() => {
                  setIsLogin(!isLogin);
                }}
                style={styles.switchButton}
              >
                <Text style={styles.switchText}>
                  {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Login"}
                </Text>
              </Button>
            </WingBlank>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    minHeight: 600,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logo: {
    fontSize: 64,
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#1F2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
  form: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  button: {
    borderRadius: 12,
    height: 48,
  },
  switchButton: {
    borderRadius: 12,
    borderColor: 'transparent',
  },
  switchText: {
    fontSize: 14,
    color: '#3B82F6',
    fontWeight: '600',
  },
});

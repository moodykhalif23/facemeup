import { useState } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";

import AuthScreen from "./src/screens/AuthScreen";
import HomeScreen from "./src/screens/HomeScreen";
import AnalysisScreen from "./src/screens/AnalysisScreen";
import QuestionnaireScreen from "./src/screens/QuestionnaireScreen";
import CameraScreen from "./src/screens/CameraScreen";
import AnalysisResultsScreen from "./src/screens/AnalysisResultsScreen";
import RecommendationsScreen from "./src/screens/RecommendationsScreen";
import ProfileScreen from "./src/screens/ProfileScreen";

const Stack = createNativeStackNavigator();

export default function App() {
  const [user, setUser] = useState(null);

  const handleAuth = (authData) => {
    setUser({
      token: authData.access_token,
      refreshToken: authData.refresh_token,
      userId: authData.user_id,
      role: authData.role,
    });
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (!user) {
    return (
      <>
        <AuthScreen onAuth={handleAuth} />
        <StatusBar style="dark" />
      </>
    );
  }

  return (
    <>
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerStyle: {
              backgroundColor: '#FFFFFF',
            },
            headerTintColor: '#1F2937',
            headerTitleStyle: {
              fontWeight: '700',
            },
            headerShadowVisible: false,
          }}
        >
          <Stack.Screen 
            name="Home" 
            options={{ headerShown: false }}
          >
            {(props) => <HomeScreen {...props} user={user} onLogout={handleLogout} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="Analysis" 
            options={{ title: 'Skin Analysis' }}
          >
            {(props) => <AnalysisScreen {...props} token={user.token} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="Questionnaire" 
            options={{ title: 'Skin Questionnaire' }}
          >
            {(props) => <QuestionnaireScreen {...props} token={user.token} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="Camera" 
            options={{ 
              title: 'Take Photo',
              headerShown: false,
            }}
          >
            {(props) => <CameraScreen {...props} token={user.token} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="AnalysisResults" 
            options={{ 
              title: 'Results',
              headerLeft: () => null,
            }}
          >
            {(props) => <AnalysisResultsScreen {...props} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="Recommendations" 
            options={{ title: 'Recommendations' }}
          >
            {(props) => <RecommendationsScreen {...props} token={user.token} />}
          </Stack.Screen>
          
          <Stack.Screen 
            name="Profile" 
            options={{ title: 'Profile History' }}
          >
            {(props) => <ProfileScreen {...props} token={user.token} userId={user.userId} />}
          </Stack.Screen>
        </Stack.Navigator>
      </NavigationContainer>
      <StatusBar style="dark" />
    </>
  );
}

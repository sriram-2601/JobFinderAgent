import React, { useState, useEffect } from 'react';
import { 
  Briefcase, CheckCircle, Clock, Percent, AlertCircle, Play, 
  RefreshCw, Award, BookOpen, Check, Copy, Calendar, User, 
  TrendingUp, BarChart2, CheckSquare, Search, Compass, FileText, ChevronRight, X, LogOut
} from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

const GoogleIcon = () => (
  <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
  </svg>
);

const FacebookIcon = () => (
  <svg className="h-5 w-5 mr-2 text-[#1877F2]" viewBox="0 0 24 24" fill="currentColor">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
  </svg>
);

const AppleIcon = () => (
  <svg className="h-5 w-5 mr-2 text-white" viewBox="0 0 24 24" fill="currentColor">
    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 4.17c.66-.81 1.11-1.93.99-3.06-1 .04-2.18.67-2.9 1.51-.62.71-1.16 1.51-1.02 2.62 1.12.09 2.27-.6 2.93-1.41z"/>
  </svg>
);

function AuthPage({ onLogin }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState(null);
  const [googleClientId, setGoogleClientId] = useState('');
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [modalView, setModalView] = useState('chooser');
  const [showCustomGoogleInput, setShowCustomGoogleInput] = useState(false);
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    const fetchConfig = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/auth/config`);
        if (res.ok) {
          const data = await res.json();
          setGoogleClientId(data.google_client_id);
        }
      } catch (err) {
        console.error("Failed to load auth config:", err);
      }
    };
    fetchConfig();

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  const handleGoogleCredentialResponse = async (response) => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: response.credential })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Google login verification failed');
      }
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('is_authenticated', 'true');
      localStorage.setItem('user_info', JSON.stringify(data.user));
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (googleClientId && window.google) {
      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse
        });
        
        const buttonElem = document.getElementById("google-signin-button");
        if (buttonElem) {
          window.google.accounts.id.renderButton(
            buttonElem,
            { 
              theme: "dark", 
              size: "large", 
              width: "380",
              text: "continue_with",
              shape: "pill"
            }
          );
        }
      } catch (e) {
        console.error("Google button rendering error:", e);
      }
    }
  }, [googleClientId, isSignUp]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (isSignUp) {
      if (!username || !password || !fullName || !email) {
        setError('All fields are required.');
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password, full_name: fullName, email }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Registration failed');
        }
        const loginRes = await fetch(`${API_BASE}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        const loginData = await loginRes.json();
        if (!loginRes.ok) {
          throw new Error(loginData.detail || 'Auto-login failed');
        }
        localStorage.setItem('auth_token', loginData.access_token);
        localStorage.setItem('is_authenticated', 'true');
        localStorage.setItem('user_info', JSON.stringify(loginData.user));
        onLogin(loginData.user);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    } else {
      if (!username || !password) {
        setError('Please fill in all fields.');
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Invalid username or password');
        }
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('is_authenticated', 'true');
        localStorage.setItem('user_info', JSON.stringify(data.user));
        onLogin(data.user);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 relative overflow-hidden select-none">
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-brand-500/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none"></div>

      <div className="max-w-md w-full z-10 animate-fade-in space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3.5 bg-brand-600 rounded-2xl shadow-xl shadow-brand-500/20 mb-3 border border-brand-500/30">
            <Briefcase className="h-8 w-8 text-white animate-pulse" />
          </div>
          <h1 className="text-3xl font-extrabold text-white font-display tracking-tight leading-tight">Antigravity</h1>
          <p className="text-sm font-semibold uppercase tracking-widest text-brand-400">JobFinder AI Platform</p>
        </div>

        <div className="glass-panel p-8 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-3xl shadow-2xl space-y-6">
          <div className="flex border-b border-slate-800 pb-1">
            <button 
              type="button"
              onClick={() => { setIsSignUp(false); setError(''); }}
              className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-all ${!isSignUp ? 'border-brand-500 text-brand-400 font-extrabold' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
            >
              Sign In
            </button>
            <button 
              type="button"
              onClick={() => { setIsSignUp(true); setError(''); }}
              className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-all ${isSignUp ? 'border-brand-500 text-brand-400 font-extrabold' : 'border-transparent text-slate-500 hover:text-slate-300'}`}
            >
              Sign Up
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl font-medium">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1.5">Full Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. John Doe"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-slate-950/60 border border-slate-850 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3 text-sm text-slate-200 outline-none transition"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1.5">Email Address</label>
                  <input 
                    type="email" 
                    placeholder="john@example.com"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950/60 border border-slate-850 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3 text-sm text-slate-200 outline-none transition"
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1.5">Username</label>
              <input 
                type="text" 
                placeholder={isSignUp ? "Choose a username" : "Enter username (e.g. admin)"}
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950/60 border border-slate-850 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3 text-sm text-slate-200 outline-none transition"
              />
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1.5">Password</label>
              <input 
                type="password" 
                placeholder={isSignUp ? "Create password" : "Enter password (e.g. admin)"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950/60 border border-slate-850 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3 text-sm text-slate-200 outline-none transition"
              />
            </div>

            {isSignUp && (
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1.5">Confirm Password</label>
                <input 
                  type="password" 
                  placeholder="Confirm your password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-slate-950/60 border border-slate-850 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl p-3 text-sm text-slate-200 outline-none transition"
                />
              </div>
            )}

            <button 
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-brand-600 hover:bg-brand-500 disabled:bg-brand-700 text-white font-bold rounded-xl shadow-lg shadow-brand-500/10 transition mt-2 flex items-center justify-center gap-2"
            >
              {loading && <RefreshCw className="h-4 w-4 animate-spin text-white" />}
              {isSignUp ? "Create Account" : "Access System"}
            </button>
          </form>

          <div className="relative flex items-center justify-center my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <span className="relative px-3 bg-[#0d1527] text-xs font-semibold text-slate-500 uppercase tracking-wider">or continue with</span>
          </div>

          <div className="space-y-2.5">
            {googleClientId ? (
              <div className="w-full flex justify-center py-1">
                <div id="google-signin-button"></div>
              </div>
            ) : (
              <button 
                type="button"
                onClick={() => setShowSetupModal(true)}
                className="w-full py-3 bg-slate-950 border border-slate-850 hover:border-slate-750 text-slate-300 font-semibold text-sm rounded-xl transition flex items-center justify-center gap-2"
              >
                <GoogleIcon />
                Continue with Google
              </button>
            )}
            <button 
              type="button"
              onClick={() => alert("Facebook authentication is currently under development.")}
              className="w-full py-3 bg-slate-950 border border-slate-850 hover:border-slate-750 text-slate-300 font-semibold text-sm rounded-xl transition flex items-center justify-center"
            >
              <FacebookIcon />
              Continue with Facebook
            </button>
            <button 
              type="button"
              onClick={() => alert("Apple authentication is currently under development.")}
              className="w-full py-3 bg-slate-950 border border-slate-850 hover:border-slate-750 text-slate-300 font-semibold text-sm rounded-xl transition flex items-center justify-center"
            >
              <AppleIcon />
              Continue with Apple
            </button>
          </div>
        </div>

        <p className="text-center text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
          Autonomous Placement ecosystem • secure sandbox mode
        </p>
      </div>

      {showSetupModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="max-w-4xl w-full bg-[#131314] border border-[#2d2d30] rounded-3xl p-8 shadow-2xl relative">
            <button 
              onClick={() => setShowSetupModal(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-slate-350 transition"
            >
              <X className="h-6 w-6" />
            </button>
            
            {modalView === 'chooser' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
                
                {/* Left Column (Google Branding) */}
                <div className="flex flex-col justify-between py-2 pr-2">
                  <div>
                    <div className="flex items-center gap-2.5 text-slate-300 text-sm font-medium">
                      <svg className="h-5 w-5" viewBox="0 0 24 24">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
                      </svg>
                      <span>Sign in with Google</span>
                    </div>
                    
                    <h2 className="text-4xl font-normal text-white mt-12 mb-3">Choose an account</h2>
                    <p className="text-sm text-slate-400">to continue to <span className="text-indigo-400 font-semibold">Antigravity JobFinder AI</span></p>
                  </div>
                  
                  <div className="mt-16 text-[10px] text-slate-500 flex items-center justify-between">
                    <span>Google Account Chooser Sandbox</span>
                    <button
                      type="button"
                      onClick={() => setModalView('setup')}
                      className="text-indigo-450 hover:text-indigo-400 font-bold uppercase tracking-wider transition"
                    >
                      Developer Credentials
                    </button>
                  </div>
                </div>
                
                {/* Right Column (Accounts List) */}
                <div className="border-t md:border-t-0 md:border-l border-[#2d2d30] pt-6 md:pt-0 md:pl-8 max-h-[380px] overflow-y-auto pr-2 space-y-0.5">
                  {[
                    { name: "Sriram Venkat", email: "sriramnbv26@gmail.com", initial: "S", color: "bg-blue-600" },
                    { name: "naruto uzumakhi", email: "narutouzumakhi85@gmail.com", initial: "n", color: "bg-purple-600" },
                    { name: "venkat", email: "venkatnbv2000@gmail.com", initial: "v", color: "bg-pink-600" },
                    { name: "Mattaparthi Sunitha", email: "sunithasd09@gmail.com", initial: "M", color: "bg-emerald-600" },
                    { name: "Geetha", email: "geethamadhuri172008@gmail.com", initial: "G", color: "bg-rose-600" },
                    { name: "Nithin Banothu", email: "bnithin638@gmail.com", initial: "N", color: "bg-amber-600" }
                  ].map((account, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setShowSetupModal(false);
                        handleGoogleCredentialResponse({ credential: `MOCK_GOOGLE_TOKEN_${account.email}` });
                      }}
                      className="w-full py-3 border-b border-[#2d2d30] hover:bg-slate-900/40 rounded-xl px-3 flex items-center gap-4 transition text-left group"
                    >
                      <div className={`h-8 w-8 rounded-full ${account.color} flex items-center justify-center text-white font-medium text-sm select-none`}>
                        {account.initial}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-semibold text-sm text-slate-200 block truncate group-hover:text-white">{account.name}</span>
                        <span className="text-xs text-slate-400 block truncate mt-0.5">{account.email}</span>
                      </div>
                    </button>
                  ))}
                  
                  {showCustomGoogleInput ? (
                    <div className="p-4 bg-slate-900/60 border border-[#2d2d30] rounded-2xl space-y-3 mt-2">
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Google Email</label>
                      <input
                        type="email"
                        placeholder="name@gmail.com"
                        value={customGoogleEmail}
                        onChange={(e) => setCustomGoogleEmail(e.target.value)}
                        className="w-full bg-slate-950 border border-[#2d2d30] focus:border-brand-500 rounded-xl p-2.5 text-xs text-slate-200 outline-none"
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setShowCustomGoogleInput(false)}
                          className="flex-1 py-2 bg-slate-800 text-slate-400 rounded-lg text-xs hover:text-slate-350"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (customGoogleEmail.trim()) {
                              setShowSetupModal(false);
                              handleGoogleCredentialResponse({ credential: `MOCK_GOOGLE_TOKEN_${customGoogleEmail.trim()}` });
                            }
                          }}
                          className="flex-1 py-2 bg-brand-600 text-white font-bold rounded-lg text-xs hover:bg-brand-500"
                        >
                          Continue
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowCustomGoogleInput(true)}
                      className="w-full py-3.5 hover:bg-slate-900/20 rounded-xl px-3 flex items-center gap-4 transition text-left text-slate-300 hover:text-white text-xs font-semibold mt-1"
                    >
                      <div className="h-8 w-8 rounded-full border border-dashed border-slate-700 flex items-center justify-center">
                        <User className="h-4 w-4 text-slate-400" />
                      </div>
                      Use another account
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-4 max-w-md mx-auto py-4">
                <div className="inline-flex p-3 bg-indigo-500/10 rounded-2xl border border-indigo-500/20 text-indigo-400">
                  <GoogleIcon />
                </div>
                <h3 className="text-xl font-bold text-white font-display">Configure Google Authentication</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  To enable real-time Google Sign-In, please configure your Google Cloud OAuth client credentials:
                </p>
                
                <div className="space-y-2 text-[11px] text-slate-300">
                  <div className="flex gap-2">
                    <span className="font-extrabold text-indigo-400 shrink-0">1.</span>
                    <span>Go to the <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="text-indigo-400 underline font-semibold">Google Cloud Console</a>.</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="font-extrabold text-indigo-400 shrink-0">2.</span>
                    <span>Create a project, then configure your **OAuth consent screen**.</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="font-extrabold text-indigo-400 shrink-0">3.</span>
                    <span>Navigate to **Credentials** &rarr; **Create Credentials** &rarr; **OAuth client ID**.</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="font-extrabold text-indigo-400 shrink-0">4.</span>
                    <span>Select **Web application**, add `http://localhost:5173` to **Authorized JavaScript origins**, and click **Create**.</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="font-extrabold text-indigo-400 shrink-0">5.</span>
                    <span>Set `GOOGLE_CLIENT_ID` in `.env` and restart the backend.</span>
                  </div>
                </div>
                
                <div className="flex gap-2 pt-4 border-t border-slate-850">
                  <button
                    type="button"
                    onClick={() => setModalView('chooser')}
                    className="flex-1 py-2 bg-slate-900 text-slate-300 rounded-xl text-xs hover:bg-slate-800 transition"
                  >
                    Back to Choose Account
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowSetupModal(false)}
                    className="flex-1 py-2 bg-slate-800 text-white font-bold rounded-xl text-xs hover:bg-slate-700 transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('is_authenticated') === 'true';
  });
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user_info');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('is_authenticated');
    localStorage.removeItem('user_info');
    localStorage.removeItem('auth_token');
    setIsAuthenticated(false);
    setUser(null);
  };

  const authFetch = async (url, options = {}) => {
    const token = localStorage.getItem('auth_token');
    const headers = {
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(url, {
      ...options,
      headers
    });
    if (res.status === 401) {
      handleLogout();
    }
    return res;
  };

  const [activeTab, setActiveTab] = useState('dashboard');
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [applications, setApplications] = useState([]);
  const [referrals, setReferrals] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [skillsGap, setSkillsGap] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [settings, setSettings] = useState({ app_mode: 'APPROVAL', smtp_username: '', telegram_chat_id: '' });
  
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [selectedApp, setSelectedApp] = useState(null);

  // Profile Form States
  const [profileForm, setProfileForm] = useState({
    name: '', email: '', phone: '', linkedin: '', github: '', portfolio: '', skills: '', experience: ''
  });

  // Resume upload states
  const [uploadState, setUploadState] = useState({ status: 'idle', error: '', progress: 0 });
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleResumeUpload(e.dataTransfer.files[0]);
    }
  };

  const handleResumeUpload = async (file) => {
    if (!file) return;

    // Enforce 10MB limit (10 * 1024 * 1024 bytes)
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setUploadState({ status: 'error', error: 'File size exceeds the 10MB limit.' });
      return;
    }

    // Enforce file extension
    const allowedExtensions = ['.pdf', '.doc', '.docx'];
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      setUploadState({ status: 'error', error: 'Invalid file type. Only PDF, DOC, and DOCX are allowed.' });
      return;
    }

    setUploadState({ status: 'uploading', error: '', progress: 10 });
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await authFetch(`${API_BASE}/api/profile/resume`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Upload failed');
      }

      setUploadState({ status: 'success', error: '', progress: 100 });
      alert("Resume uploaded successfully!");
      fetchData(); // Refresh profile information
    } catch (err) {
      setUploadState({ status: 'error', error: err.message });
    }
  };

  // Scheduling Form States
  const [schedForm, setSchedForm] = useState({
    application_id: '', stage: 'OA', scheduled_at: '', notes: ''
  });

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [activeTab, isAuthenticated]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const resProfile = await authFetch(`${API_BASE}/api/profile`);
      if (resProfile.ok) {
        const data = await resProfile.json();
        setProfile(data);
        setProfileForm({
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          linkedin: data.linkedin || '',
          github: data.github || '',
          portfolio: data.portfolio || '',
          skills: data.skills || '',
          experience: data.experience || ''
        });
      }

      const resJobs = await authFetch(`${API_BASE}/api/jobs`);
      if (resJobs.ok) setJobs(await resJobs.json());

      const resMatches = await authFetch(`${API_BASE}/api/matches`);
      if (resMatches.ok) setMatches(await resMatches.json());

      const resApps = await authFetch(`${API_BASE}/api/applications`);
      if (resApps.ok) setApplications(await resApps.json());

      const resRefs = await authFetch(`${API_BASE}/api/referrals`);
      if (resRefs.ok) setReferrals(await resRefs.json());

      const resInts = await authFetch(`${API_BASE}/api/interviews`);
      if (resInts.ok) setInterviews(await resInts.json());

      const resGap = await authFetch(`${API_BASE}/api/skills-gap`);
      if (resGap.ok) setSkillsGap(await resGap.json());

      const resAnal = await authFetch(`${API_BASE}/api/analytics`);
      if (resAnal.ok) setAnalytics(await resAnal.json());

      const resSet = await authFetch(`${API_BASE}/api/settings`);
      if (resSet.ok) setSettings(await resSet.json());

    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    }
    setLoading(false);
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    try {
      const res = await authFetch(`${API_BASE}/api/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm),
      });
      if (res.ok) {
        alert("Candidate Profile updated successfully!");
        fetchData();
      }
    } catch (err) {
      alert("Failed to update profile: " + err.message);
    }
  };

  const handleToggleMode = async () => {
    const newMode = settings.app_mode === 'APPROVAL' ? 'AUTONOMOUS' : 'APPROVAL';
    try {
      const res = await authFetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...settings, app_mode: newMode }),
      });
      if (res.ok) {
        setSettings({ ...settings, app_mode: newMode });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerJobHunter = async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/trigger-search`, { method: 'POST' });
      if (res.ok) {
        alert("Job discovery crawl initiated in the background! Matches will evaluate in a few minutes.");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerInboxScan = async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/trigger-inbox-scan`, { method: 'POST' });
      if (res.ok) {
        alert("IMAP scan triggered! Interview tracker is synchronizing matching emails.");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerEmailJobScan = async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/trigger-email-job-scan`, { method: 'POST' });
      if (res.ok) {
        alert("Email Job Scan triggered! Inspecting emails for new career links and opportunities.");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleApproveMatch = async (matchId) => {
    try {
      const res = await authFetch(`${API_BASE}/api/matches/${matchId}/approve`, { method: 'POST' });
      if (res.ok) {
        alert("Match approved! Form filler application pipeline initiated.");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRejectMatch = async (matchId) => {
    try {
      const res = await authFetch(`${API_BASE}/api/matches/${matchId}/reject`, { method: 'POST' });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddInterview = async (e) => {
    e.preventDefault();
    try {
      const res = await authFetch(`${API_BASE}/api/interviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          application_id: parseInt(schedForm.application_id),
          stage: schedForm.stage,
          scheduled_at: schedForm.scheduled_at,
          notes: schedForm.notes
        }),
      });
      if (res.ok) {
        alert("Interview successfully scheduled!");
        setSchedForm({ application_id: '', stage: 'OA', scheduled_at: '', notes: '' });
        fetchData();
      }
    } catch (err) {
      alert("Failed to schedule interview: " + err.message);
    }
  };

  // Helper copy text
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Outreach message copied to clipboard!");
  };

  // Filter Discovered Jobs
  const filteredJobs = jobs.filter(j => 
    j.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.job_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isAuthenticated) {
    return <AuthPage onLogin={handleLogin} />;
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      
      {/* SIDEBAR NAVIGATION */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/40 backdrop-blur-md p-6 flex flex-col justify-between shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2.5 bg-brand-600 rounded-lg shadow-md shadow-brand-500/20">
              <Briefcase className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight">Antigravity</h1>
              <span className="text-xs text-brand-400 font-semibold uppercase tracking-wider">JobFinder AI</span>
            </div>
          </div>
          
          <nav className="space-y-1">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: Compass },
              { id: 'jobs', name: 'Jobs Found', icon: Search },
              { id: 'matches', name: 'Matched Jobs', icon: Award },
              { id: 'applied', name: 'Applied History', icon: CheckCircle },
              { id: 'referrals', name: 'Outreach & Referrals', icon: User },
              { id: 'tracker', name: 'Interview Tracker', icon: Calendar },
              { id: 'skills', name: 'Skill Gap & Roadmap', icon: BookOpen },
              { id: 'analytics', name: 'Analytics', icon: BarChart2 },
              { id: 'profile', name: 'My Profile', icon: FileText }
            ].map(tab => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSelectedMatch(null); setSelectedApp(null); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    active 
                      ? 'bg-brand-600/15 border border-brand-500/30 text-brand-300 font-semibold' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${active ? 'text-brand-400' : 'text-slate-500'}`} />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Global Settings Status Panel */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400">Application Mode</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
              settings.app_mode === 'AUTONOMOUS' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
            }`}>
              {settings.app_mode}
            </span>
          </div>
          <button 
            onClick={handleToggleMode}
            className="w-full text-center py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg transition"
          >
            Switch to {settings.app_mode === 'APPROVAL' ? 'Autonomous' : 'Approval'}
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full">
        
        {/* HEADER SECTION */}
        <header className="flex justify-between items-center mb-8 border-b border-slate-800/60 pb-6">
          <div>
            <h2 className="text-2xl font-bold font-display text-white capitalize">{activeTab.replace('-', ' ')}</h2>
            <p className="text-sm text-slate-400 mt-1">Autonomous candidate sourcing and placement ecosystem</p>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={triggerInboxScan}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-sm font-semibold transition"
            >
              <RefreshCw className="h-4 w-4 text-slate-400" />
              Sync Gmail IMAP
            </button>
            <button 
              onClick={triggerEmailJobScan}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-sm font-semibold transition"
            >
              <Search className="h-4 w-4 text-indigo-400" />
              Scan Job Emails
            </button>
            <button 
              onClick={triggerJobHunter}
              className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-sm font-bold shadow-md shadow-brand-600/10 transition"
            >
              <Play className="h-4 w-4 fill-white" />
              Trigger Job Hunter
            </button>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-rose-600/15 border border-rose-500/20 hover:bg-rose-600/20 text-rose-300 rounded-lg text-sm font-bold transition"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </header>

        {/* LOADING SHIM */}
        {loading && (
          <div className="flex items-center gap-2 py-3 px-4 bg-brand-600/10 border border-brand-500/20 text-brand-300 rounded-xl mb-6 text-sm">
            <RefreshCw className="h-4 w-4 animate-spin text-brand-400" />
            Updating portal tables...
          </div>
        )}

        {/* TAB CONTENTS */}
        
        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && analytics && (
          <div className="space-y-8 animate-fade-in">
            {/* STAT CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                { name: "Total Jobs Crawled", val: analytics.summary.jobs_found, icon: Search, color: "text-blue-400" },
                { name: "Applications Submitted", val: analytics.summary.jobs_applied, icon: CheckCircle, color: "text-emerald-400", substats: true },
                { name: "Active Interviews / OAs", val: analytics.summary.interview_requests, icon: Calendar, color: "text-purple-400" },
                { name: "Callback Response Rate", val: `${analytics.summary.response_rate}%`, icon: Percent, color: "text-brand-400" }
              ].map((c, i) => {
                const Icon = c.icon;
                return (
                  <div key={i} className="glass-panel p-6 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-semibold text-slate-400">{c.name}</span>
                        <Icon className={`h-5 w-5 ${c.color}`} />
                      </div>
                      <div className="text-3xl font-bold mt-4 text-white font-display">{c.val}</div>
                    </div>
                    {c.substats && (
                      <div className="flex justify-between items-center gap-1.5 mt-4 pt-3 border-t border-slate-800/60 text-[10px] text-slate-400 font-semibold uppercase tracking-wide">
                        <div>Today: <span className="text-emerald-400 font-extrabold">{analytics.summary.applied_daily}</span></div>
                        <div>Week: <span className="text-emerald-400 font-extrabold">{analytics.summary.applied_weekly}</span></div>
                        <div>Month: <span className="text-emerald-400 font-extrabold">{analytics.summary.applied_monthly}</span></div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* APPLICATION VOLUME BREAKDOWN */}
            <div className="glass-panel p-6 bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl">
              <h3 className="text-base font-bold text-white font-display mb-4 flex items-center gap-2">
                <BarChart2 className="h-5 w-5 text-emerald-400" />
                Application Volume Metrics
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Today (24h)", val: analytics.summary.applied_daily, desc: "Last 24 hours", color: "from-emerald-500/10 to-teal-500/5 text-emerald-400 border-emerald-500/20" },
                  { label: "This Week (7d)", val: analytics.summary.applied_weekly, desc: "Last 7 days", color: "from-blue-500/10 to-indigo-500/5 text-blue-400 border-blue-500/20" },
                  { label: "This Month (30d)", val: analytics.summary.applied_monthly, desc: "Last 30 days", color: "from-purple-500/10 to-pink-500/5 text-purple-400 border-purple-500/20" },
                  { label: "All Time (Total)", val: analytics.summary.jobs_applied, desc: "Total submitted", color: "from-brand-500/10 to-violet-500/5 text-brand-400 border-brand-500/20" }
                ].map((item, idx) => (
                  <div key={idx} className={`p-4 bg-gradient-to-br ${item.color} border rounded-xl flex flex-col justify-between hover:scale-[1.02] transition-all duration-200`}>
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">{item.label}</span>
                      <span className="text-2xl font-bold font-display mt-2 block">{item.val}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-2 block">{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* AI AGENTS REGISTRY & ORCHESTRATION */}
            <div className="glass-panel p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></div>
                <h3 className="text-lg font-bold text-white font-display">Active AI Agents Registry</h3>
                <span className="text-xs text-slate-400 ml-1.5">(7 Modular Agents Orchestrated 24/7)</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                  {
                    id: 1,
                    name: "Agent 1: Job Hunter",
                    status: "ACTIVE",
                    statusColor: "text-emerald-400 bg-emerald-500/10",
                    pulseColor: "bg-emerald-400",
                    task: "Crawls Greenhouse, Lever, LinkedIn, Indeed, Upwork, and RSS feeds for entry-level IT roles.",
                    action: triggerJobHunter,
                    btnLabel: "Crawl Now"
                  },
                  {
                    id: 2,
                    name: "Agent 2: AI Matcher",
                    status: "STANDBY",
                    statusColor: "text-blue-400 bg-blue-500/10",
                    pulseColor: "bg-blue-400",
                    task: "Evaluates descriptions using Gemini, computes matching score, applies priority boosts.",
                    action: null,
                    btnLabel: "Triggered on discovery"
                  },
                  {
                    id: 3,
                    name: "Agent 3: Auto Applier",
                    status: "STANDBY",
                    statusColor: "text-blue-400 bg-blue-500/10",
                    pulseColor: "bg-blue-400",
                    task: "Auto-fills Greenhouse/Lever portal fields, uploads resume, answers screening questions.",
                    action: null,
                    btnLabel: "Triggered on match"
                  },
                  {
                    id: 4,
                    name: "Agent 4: Notifier",
                    status: "ACTIVE",
                    statusColor: "text-emerald-400 bg-emerald-500/10",
                    pulseColor: "bg-emerald-400",
                    task: "Dispatches instant Telegram/SMTP alerts, logs screenshots, sends Daily/Weekly summaries.",
                    action: null,
                    btnLabel: "Instant + 10 PM Daily"
                  },
                  {
                    id: 5,
                    name: "Agent 5: Referral Finder",
                    status: "STANDBY",
                    statusColor: "text-blue-400 bg-blue-500/10",
                    pulseColor: "bg-blue-400",
                    task: "Queries LinkedIn search for recruiters and pre-drafts custom referral request outreach templates.",
                    action: null,
                    btnLabel: "Runs for match >= 85%"
                  },
                  {
                    id: 6,
                    name: "Agent 6: Skill Analyzer",
                    status: "ACTIVE",
                    statusColor: "text-emerald-400 bg-emerald-500/10",
                    pulseColor: "bg-emerald-400",
                    task: "Aggregates missing skills from crawl datasets and ranks weekly learning study roadmap items.",
                    action: () => setActiveTab('skills'),
                    btnLabel: "View Roadmap"
                  },
                  {
                    id: 7,
                    name: "Agent 7: Tracker",
                    status: "ACTIVE",
                    statusColor: "text-emerald-400 bg-emerald-500/10",
                    pulseColor: "bg-emerald-400",
                    task: "Checks Gmail inbox via IMAP, schedules next rounds, alerts dates and times of interviews.",
                    action: triggerInboxScan,
                    btnLabel: "Sync Inbox"
                  }
                ].map(agent => (
                  <div key={agent.id} className="p-4 bg-slate-950/60 border border-slate-850 rounded-xl flex flex-col justify-between hover:border-slate-800 transition">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-white">{agent.name}</span>
                        <span className={`inline-flex items-center gap-1.5 text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full ${agent.statusColor}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${agent.pulseColor} animate-pulse`}></span>
                          {agent.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-normal mb-4">{agent.task}</p>
                    </div>
                    {agent.action ? (
                      <button 
                        onClick={agent.action}
                        className="w-full text-center py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 text-[10px] font-bold rounded-lg transition text-slate-300"
                      >
                        {agent.btnLabel}
                      </button>
                    ) : (
                      <span className="w-full text-center py-1.5 bg-slate-900/20 text-[10px] font-semibold rounded-lg text-slate-500 block">
                        {agent.btnLabel}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* DASHBOARD CHARTS & RECENT ACTIVITIES */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* Left Column: Top Roles & Sources list */}
              <div className="md:col-span-2 space-y-8">
                
                {/* Top Roles Distribution */}
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-bold mb-4">Discovered Roles Categories</h3>
                  <div className="space-y-4">
                    {analytics.top_roles.map((r, i) => (
                      <div key={i}>
                        <div className="flex justify-between text-sm mb-1.5 font-medium">
                          <span>{r.category}</span>
                          <span className="text-slate-400">{r.count} postings</span>
                        </div>
                        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                          <div 
                            className="bg-brand-500 h-full rounded-full" 
                            style={{ width: `${Math.min((r.count / (analytics.summary.jobs_found || 1)) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top Job Crawling Sources */}
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-bold mb-4">Discovery Channels share</h3>
                  <div className="grid grid-cols-5 gap-4">
                    {analytics.top_sources.map((s, i) => (
                      <div key={i} className="text-center p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                        <div className="text-2xl font-bold text-white font-display">{s.count}</div>
                        <div className="text-xs text-slate-400 mt-1 truncate">{s.source}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: Platform Event Logs */}
              <div className="glass-panel p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-bold mb-4">Latest Application Updates</h3>
                  <div className="space-y-4">
                    {applications.slice(0, 5).map((app, i) => (
                      <div key={i} className="flex gap-3 border-b border-slate-800/40 pb-4 last:border-0 last:pb-0">
                        <div className={`p-2 rounded-lg mt-0.5 shrink-0 ${
                          app.status === 'APPLIED' ? 'bg-emerald-500/10 text-emerald-400' : 
                          app.status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400' : 'bg-purple-500/10 text-purple-400'
                        }`}>
                          <CheckSquare className="h-4 w-4" />
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-white leading-tight">{app.job_title}</h4>
                          <p className="text-xs text-slate-400 mt-0.5">{app.company_name} • {app.location}</p>
                          <span className="text-[10px] uppercase font-bold text-slate-500 mt-1 block">{app.applied_at}</span>
                        </div>
                      </div>
                    ))}
                    {applications.length === 0 && (
                      <div className="text-center text-slate-500 text-sm py-12">No active applications submitted yet.</div>
                    )}
                  </div>
                </div>
                <button 
                  onClick={() => setActiveTab('applied')}
                  className="w-full text-center py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg transition mt-6"
                >
                  View Full History
                </button>
              </div>

            </div>
          </div>
        )}

        {/* TAB 2: DISCOVERED JOBS LIST */}
        {activeTab === 'jobs' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Search jobs by company, role, or location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-800 focus:border-brand-500 rounded-lg text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <div className="glass-panel max-h-[calc(100vh-260px)] overflow-y-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900 sticky top-0 z-10 shadow-sm">
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Company</th>
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Role / Description</th>
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Location</th>
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Discovered</th>
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Source</th>
                    <th className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Job Link</th>
                    <th className="text-center text-xs font-bold text-slate-400 uppercase tracking-wider py-4 px-6">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((job) => (
                    <tr key={job.id} className="border-b border-slate-800/40 hover:bg-slate-900/20 transition">
                      <td className="py-4 px-6 font-semibold text-white">{job.company_name}</td>
                      <td className="py-4 px-6">
                        <div className="max-w-md">
                          <div className="text-sm font-semibold text-slate-200">{job.job_title}</div>
                          <span className="text-[10px] text-brand-400 font-bold uppercase mt-0.5 block">{job.job_type}</span>
                          {job.description && (
                            <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                              {job.description}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-6 text-sm text-slate-400">{job.location}</td>
                      <td className="py-4 px-6 text-sm text-slate-400">{job.discovered_at}</td>
                      <td className="py-4 px-6">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-medium">
                          {job.source}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <a 
                          href={job.apply_link} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-xs text-brand-400 hover:text-brand-300 hover:underline font-semibold inline-flex items-center gap-1"
                        >
                          View Link <ChevronRight className="h-3 w-3" />
                        </a>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <button
                          onClick={async () => {
                            await fetch(`${API_BASE}/api/jobs/${job.id}/evaluate`, { method: 'POST' });
                            alert("Triggered AI match analysis for this job. Check Matched Jobs shortly.");
                          }}
                          className="px-3 py-1.5 bg-brand-600/10 hover:bg-brand-600/25 border border-brand-500/20 text-brand-300 rounded-lg text-xs font-bold transition"
                        >
                          Analyze Match
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredJobs.length === 0 && (
                    <tr>
                      <td colSpan="7" className="text-center text-slate-500 py-16 text-sm">No jobs matches the criteria found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: MATCHED JOBS DETAILS */}
        {activeTab === 'matches' && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* MATCH LISTING TABLE */}
              <div className="md:col-span-2 space-y-4 max-h-[calc(100vh-240px)] overflow-y-auto pr-2">
                {matches.map((m) => {
                  const score = m.match_score;
                  const color = score >= 80 ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5' : 
                                (score >= 70 ? 'border-amber-500/30 text-amber-400 bg-amber-500/5' : 'border-rose-500/30 text-rose-400 bg-rose-500/5');
                  return (
                    <div 
                      key={m.match_id} 
                      onClick={() => setSelectedMatch(m)}
                      className={`p-5 rounded-xl border transition-all cursor-pointer hover:scale-[1.01] ${
                        selectedMatch?.match_id === m.match_id ? 'border-brand-500 bg-brand-600/5' : 'border-slate-800 bg-slate-900/40'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-base font-bold text-white leading-tight">{m.job_title}</h3>
                          <p className="text-sm text-slate-400 mt-1">{m.company_name} • {m.location}</p>
                        </div>
                        <div className={`px-3 py-1.5 border rounded-lg font-display font-extrabold text-sm ${color}`}>
                          {score}%
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center mt-5 pt-4 border-t border-slate-800/60">
                        <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
                          m.match_status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400' :
                          m.match_status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400' : 'bg-amber-500/10 text-amber-400'
                        }`}>
                          {m.match_status}
                        </span>
                        
                        <div className="flex gap-2">
                          {m.match_status === 'PENDING_REVIEW' && (
                            <>
                              <button 
                                onClick={(e) => { e.stopPropagation(); handleRejectMatch(m.match_id); }}
                                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-rose-400 text-xs font-semibold rounded"
                              >
                                Reject
                              </button>
                              <button 
                                onClick={(e) => { e.stopPropagation(); handleApproveMatch(m.match_id); }}
                                className="px-3 py-1 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded"
                              >
                                Approve & Apply
                              </button>
                            </>
                          )}
                          <a 
                            href={m.apply_link} 
                            target="_blank" 
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded"
                          >
                            Post Link
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {matches.length === 0 && (
                  <div className="glass-panel text-center text-slate-500 py-24">No job matching scores generated yet. Trigger Job Hunter to fetch jobs.</div>
                )}
              </div>

              {/* DETAILS AND OPTIMIZATIONS SIDE PANEL */}
              <div className="glass-panel p-6 h-fit max-h-[calc(100vh-240px)] overflow-y-auto sticky top-8">
                {selectedMatch ? (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white">{selectedMatch.job_title}</h3>
                      <p className="text-sm text-slate-400 mt-1">{selectedMatch.company_name}</p>
                    </div>

                    <div className="border-t border-slate-800 pt-4 flex gap-2">
                      <a 
                        href={selectedMatch.apply_link} 
                        target="_blank" 
                        rel="noreferrer"
                        className="w-full text-center py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-lg transition"
                      >
                        Apply / View Job Link
                      </a>
                    </div>

                    {selectedMatch.description && (
                      <div className="border-t border-slate-800 pt-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Job Description</h4>
                        <div className="text-xs text-slate-300 bg-slate-950/60 p-4 border border-slate-800 rounded-lg leading-relaxed max-h-48 overflow-y-auto font-sans">
                          {selectedMatch.description}
                        </div>
                      </div>
                    )}

                    <div className="border-t border-slate-800 pt-4">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Resume Optimization Tips</h4>
                      <p className="text-sm text-slate-200 leading-relaxed bg-slate-950/60 p-4 border border-slate-800 rounded-lg">{selectedMatch.optimize_suggestions || "None suggested."}</p>
                    </div>

                    <div className="border-t border-slate-800 pt-4">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Tailored Cover Letter</h4>
                      <div className="relative">
                        <textarea 
                          readOnly 
                          value={selectedMatch.cover_letter}
                          className="w-full h-48 bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 leading-relaxed resize-none outline-none font-mono"
                        />
                        <button 
                          onClick={() => copyToClipboard(selectedMatch.cover_letter)}
                          className="absolute right-2 top-2 p-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {selectedMatch.missing_skills && (
                      <div className="border-t border-slate-800 pt-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Missing Skills Extracted</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedMatch.missing_skills.split(",").map((sk, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 font-medium capitalize">
                              {sk.strip ? sk.strip() : sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-slate-500 py-32 text-sm">
                    Select a matched job on the left to view optimization guides and pre-generated cover letters.
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* TAB 4: APPLIED HISTORY */}
        {activeTab === 'applied' && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* APPLICATIONS LIST */}
              <div className="md:col-span-2 space-y-4 max-h-[calc(100vh-240px)] overflow-y-auto pr-2">
                {applications.map((app) => (
                  <div 
                    key={app.id}
                    onClick={() => setSelectedApp(app)}
                    className={`p-5 rounded-xl border transition-all cursor-pointer hover:scale-[1.01] ${
                      selectedApp?.id === app.id ? 'border-brand-500 bg-brand-600/5' : 'border-slate-800 bg-slate-900/40'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-base font-bold text-white leading-tight">{app.job_title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-slate-400">{app.company_name} • {app.location}</span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-extrabold uppercase ${
                            app.source && app.source.toLowerCase().includes("email") 
                              ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" 
                              : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          }`}>
                            {app.source && app.source.toLowerCase().includes("email") ? "Email" : "Internet"}
                          </span>
                        </div>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
                        app.status === 'APPLIED' ? 'bg-emerald-500/10 text-emerald-400' :
                        app.status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400' : 'bg-purple-500/10 text-purple-400'
                      }`}>
                        {app.status}
                      </span>
                    </div>

                    <div className="flex justify-between items-center mt-5 pt-4 border-t border-slate-800/60 text-xs text-slate-400">
                      <span>Applied: {app.applied_at}</span>
                      <span>Confirmation: <strong className="text-slate-200">{app.confirmation_number || 'N/A'}</strong></span>
                    </div>
                  </div>
                ))}
                {applications.length === 0 && (
                  <div className="glass-panel text-center text-slate-500 py-24">No applications submitted yet. Approve matches or toggle Autonomous mode.</div>
                )}
              </div>

              {/* APPLIED EVIDENCE LIGHTBOX PANEL */}
              <div className="glass-panel p-6 h-fit max-h-[calc(100vh-240px)] overflow-y-auto sticky top-8">
                {selectedApp ? (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-bold text-white">{selectedApp.job_title}</h3>
                      <p className="text-sm text-slate-400 mt-1">{selectedApp.company_name}</p>
                    </div>

                    {selectedApp.description && (
                      <div className="border-t border-slate-800 pt-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Job Description</h4>
                        <div className="text-xs text-slate-300 bg-slate-950/60 p-4 border border-slate-800 rounded-lg leading-relaxed max-h-40 overflow-y-auto font-sans">
                          {selectedApp.description}
                        </div>
                      </div>
                    )}

                    <div className="border-t border-slate-800 pt-4">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Application Screenshot Confirmation</h4>
                      {selectedApp.screenshot_url ? (
                        <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
                          {/* If screenshot exists, display static hosted image */}
                          {selectedApp.screenshot_path.includes("Simulated") ? (
                            <div className="flex flex-col items-center justify-center p-12 text-slate-500">
                              <CheckCircle className="h-12 w-12 text-emerald-500 mb-2" />
                              <span className="text-xs">Mock Application Proof Simulated Successfully</span>
                            </div>
                          ) : (
                            <img 
                              src={`${API_BASE}${selectedApp.screenshot_url}`} 
                              alt="Submission Confirmation"
                              className="w-full h-auto max-h-64 object-cover"
                            />
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-slate-500 border border-dashed border-slate-800 rounded-lg py-12 text-xs">
                          No screenshot logged.
                        </div>
                      )}
                    </div>

                    {selectedApp.response_message && (
                      <div className="border-t border-slate-800 pt-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Portal Response Message</h4>
                        <div className="text-xs text-emerald-400 bg-emerald-500/5 border border-emerald-500/10 p-3.5 rounded-lg leading-relaxed font-mono">
                          {selectedApp.response_message}
                        </div>
                      </div>
                    )}

                    {selectedApp.email_confirmation_subject && (
                      <div className="border-t border-slate-800 pt-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Synced Email Confirmation</h4>
                        <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-3.5 space-y-2">
                          <div className="flex justify-between items-center text-[10px] font-semibold">
                            <span className="text-brand-300 truncate max-w-[150px]">{selectedApp.email_confirmation_sender}</span>
                            <span className="text-slate-500 shrink-0">{selectedApp.email_confirmation_date}</span>
                          </div>
                          <div className="text-xs font-bold text-white leading-snug">{selectedApp.email_confirmation_subject}</div>
                          {selectedApp.email_confirmation_snippet && (
                            <p className="text-[11px] text-slate-400 leading-normal italic font-mono pt-2 border-t border-slate-850/40">
                              "{selectedApp.email_confirmation_snippet.length > 180 ? selectedApp.email_confirmation_snippet.slice(0, 180) + '...' : selectedApp.email_confirmation_snippet}"
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="border-t border-slate-800 pt-4 flex justify-between items-center text-xs text-slate-400">
                      <span>Discovery Source:</span>
                      <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${
                        selectedApp.source && selectedApp.source.toLowerCase().includes("email")
                          ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                          : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                      }`}>
                        {selectedApp.source && selectedApp.source.toLowerCase().includes("email") ? "Email" : "Internet"}
                      </span>
                    </div>

                    <div className="border-t border-slate-800 pt-4 flex gap-2">
                      <a 
                        href={selectedApp.apply_link} 
                        target="_blank" 
                        rel="noreferrer"
                        className="w-full text-center py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-lg transition"
                      >
                        Original Job Link
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-slate-500 py-32 text-sm">
                    Select an application on the left to inspect confirmation codes, logged states, and screenshot evidence.
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* TAB 5: REFERRALS & OUTREACH MESSAGES */}
        {activeTab === 'referrals' && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* CONTACT DETAILS PANEL */}
              <div className="space-y-4">
                <h3 className="text-lg font-bold mb-2">Outreach Contact Database</h3>
                <div className="space-y-4 max-h-[calc(100vh-280px)] overflow-y-auto pr-2">
                  {referrals.map((ref) => (
                    <div key={ref.id} className="glass-panel p-5 space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-base font-bold text-white">{ref.contact_name}</h4>
                        <p className="text-sm text-slate-400 mt-0.5">{ref.contact_title}</p>
                        <p className="text-xs text-brand-400 font-medium mt-1">For Role: {ref.job_title} at {ref.company_name}</p>
                      </div>
                      <span className="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded font-extrabold uppercase">
                        {ref.status}
                      </span>
                    </div>

                    <div className="border-t border-slate-800/60 pt-4 flex items-center justify-between text-xs">
                      <a 
                        href={ref.contact_info} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-brand-400 hover:underline inline-flex items-center gap-1 font-semibold"
                      >
                        Open LinkedIn Profile <ChevronRight className="h-3 w-3" />
                      </a>
                      
                      <div className="flex gap-2">
                        <button 
                          onClick={() => copyToClipboard(ref.referral_message)}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded"
                        >
                          Copy Ref Ask
                        </button>
                        <button 
                          onClick={() => copyToClipboard(ref.recruiter_message)}
                          className="px-2.5 py-1 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded"
                        >
                          Copy Pitch
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {referrals.length === 0 && (
                  <div className="glass-panel text-center text-slate-500 py-24">No outreach targets identified. Trigger match evaluations to identify contacts.</div>
                )}
                </div>
              </div>

              {/* MESSAGES PREVIEW AREA */}
              <div className="glass-panel p-6 h-fit max-h-[calc(100vh-240px)] overflow-y-auto">
                <h3 className="text-lg font-bold mb-4">Referrals & outreach Pitch Guide</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  For matching scores higher than 85%, the Referral Finder queries recruiters at target startup platforms and designs custom messages. 
                  Use these templates on LinkedIn to maximize response ratios.
                </p>
                <div className="p-4 bg-brand-600/5 border border-brand-500/10 rounded-xl space-y-2">
                  <span className="text-xs font-extrabold text-brand-400 uppercase tracking-wider">Strategy Recommendation</span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    1. **Connect with the recruiter** using the pre-generated direct pitch.
                    2. If they do not accept, find a Software Engineer at the company and ask for a referral using the "Copy Ref Ask" text block.
                  </p>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 6: INTERVIEW TRACKER */}
        {activeTab === 'tracker' && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* SCHEDULER FORM PANEL */}
              <div className="glass-panel p-6 h-fit max-h-[calc(100vh-240px)] overflow-y-auto">
                <h3 className="text-lg font-bold mb-4">Log Interview Milestone</h3>
                <form onSubmit={handleAddInterview} className="space-y-4">
                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Target Application</label>
                    <select 
                      required
                      value={schedForm.application_id}
                      onChange={(e) => setSchedForm({ ...schedForm, application_id: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-300 outline-none"
                    >
                      <option value="">Select Company / Role</option>
                      {applications.map(app => (
                        <option key={app.id} value={app.id}>{app.company_name} - {app.job_title}</option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Stage</label>
                      <select 
                        required
                        value={schedForm.stage}
                        onChange={(e) => setSchedForm({ ...schedForm, stage: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-300 outline-none"
                      >
                        <option value="OA">Coding Assessment</option>
                        <option value="TECHNICAL">Technical Interview</option>
                        <option value="HR">HR / Fit Check</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Scheduled At</label>
                      <input 
                        type="datetime-local" 
                        required
                        value={schedForm.scheduled_at}
                        onChange={(e) => setSchedForm({ ...schedForm, scheduled_at: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-300 outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Notes / Zoom Details</label>
                    <textarea 
                      placeholder="Paste meeting details, links, or preparations notes here..."
                      value={schedForm.notes}
                      onChange={(e) => setSchedForm({ ...schedForm, notes: e.target.value })}
                      className="w-full h-24 bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-300 outline-none resize-none"
                    />
                  </div>

                  <button 
                    type="submit"
                    className="w-full text-center py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-lg transition"
                  >
                    Register Event
                  </button>
                </form>
              </div>

              {/* TIMELINE LIST */}
              <div className="md:col-span-2 space-y-4">
                <h3 className="text-lg font-bold mb-2">Upcoming Events Timeline</h3>
                <div className="space-y-4 max-h-[calc(100vh-280px)] overflow-y-auto pr-2">
                  {interviews.map((item) => (
                    <div key={item.id} className="glass-panel p-5 flex gap-4">
                    <div className="p-3 bg-brand-600/10 text-brand-400 rounded-xl h-fit border border-brand-500/10 shrink-0">
                      <Calendar className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded">
                          {item.stage}
                        </span>
                        <h4 className="text-base font-bold text-white leading-tight">{item.job_title} at {item.company_name}</h4>
                      </div>
                      
                      <p className="text-xs text-brand-400 font-bold mt-2">Time: {item.scheduled_at}</p>
                      
                      {item.notes && (
                        <p className="text-xs text-slate-400 mt-2 bg-slate-950/60 p-3 rounded-lg border border-slate-800/60 font-mono leading-relaxed">
                          {item.notes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                {interviews.length === 0 && (
                  <div className="glass-panel text-center text-slate-500 py-24">No scheduled events logged. Tracker scans Gmail IMAP inbox automatically.</div>
                )}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 7: SKILL GAP & ROADMAPS */}
        {activeTab === 'skills' && skillsGap && (
          <div className="space-y-6 animate-fade-in">
            <h3 className="text-lg font-display font-bold">In-Demand Skills Roadmaps</h3>
            <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
              We compile missing technical skills across all crawled job postings. Learning these technologies will optimize resume matching score directly.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* ROADMAP TIMELINE */}
              <div className="md:col-span-2 space-y-4 max-h-[calc(100vh-240px)] overflow-y-auto pr-2">
                {skillsGap.trending_missing_skills.map((item) => (
                  <div key={item.rank} className="glass-panel p-5 flex gap-4 hover:scale-[1.005] transition-all">
                    <div className="h-10 w-10 bg-slate-950 border border-slate-850 rounded-lg flex items-center justify-center font-display font-extrabold text-sm text-brand-400 shrink-0">
                      #{item.rank}
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-white">{item.skill_name}</h4>
                      <p className="text-xs text-slate-400 mt-0.5">Found in `{item.job_mentions}` discovered job posts</p>
                      
                      <div className="flex gap-4 mt-4 text-xs">
                        <div>
                          <span className="text-slate-500 font-semibold uppercase">Resource:</span>
                          <span className="text-slate-300 font-medium ml-1.5">{item.recommended_resource}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 font-semibold uppercase">Est. Learning Time:</span>
                          <span className="text-brand-400 font-bold ml-1.5">{item.suggested_hours} Hours</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* INSIGHT CARD */}
              <div className="glass-panel p-6 h-fit max-h-[calc(100vh-240px)] overflow-y-auto space-y-4">
                <h3 className="text-lg font-bold text-white">Roadmap Analytics</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  These missing elements are extracted directly from active fresher listings. To update your profile, add certifications or project accomplishments in the **My Profile** tab.
                </p>
                
                <div className="p-4 bg-brand-600/5 border border-brand-500/10 rounded-xl">
                  <span className="text-xs font-extrabold text-brand-400 uppercase tracking-wider block mb-1">Top Recommendation</span>
                  <p className="text-xs text-slate-200 leading-relaxed font-semibold">
                    Prioritize studying AWS Cloud configurations and Docker containers as they represent the most common entry requirements.
                  </p>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 8: ANALYTICS DETAIL PAGE */}
        {activeTab === 'analytics' && analytics && (
          <div className="space-y-8 animate-fade-in">
            {/* APPLICATION VOLUME BREAKDOWN */}
            <div className="glass-panel p-6 bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl">
              <h3 className="text-base font-bold text-white font-display mb-4 flex items-center gap-2">
                <BarChart2 className="h-5 w-5 text-emerald-400" />
                Application Volume Metrics
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Today (24h)", val: analytics.summary.applied_daily, desc: "Last 24 hours", color: "from-emerald-500/10 to-teal-500/5 text-emerald-400 border-emerald-500/20" },
                  { label: "This Week (7d)", val: analytics.summary.applied_weekly, desc: "Last 7 days", color: "from-blue-500/10 to-indigo-500/5 text-blue-400 border-blue-500/20" },
                  { label: "This Month (30d)", val: analytics.summary.applied_monthly, desc: "Last 30 days", color: "from-purple-500/10 to-pink-500/5 text-purple-400 border-purple-500/20" },
                  { label: "All Time (Total)", val: analytics.summary.jobs_applied, desc: "Total submitted", color: "from-brand-500/10 to-violet-500/5 text-brand-400 border-brand-500/20" }
                ].map((item, idx) => (
                  <div key={idx} className={`p-4 bg-gradient-to-br ${item.color} border rounded-xl flex flex-col justify-between hover:scale-[1.02] transition-all duration-200`}>
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">{item.label}</span>
                      <span className="text-2xl font-bold font-display mt-2 block">{item.val}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-2 block">{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* Score Distribution list */}
              <div className="glass-panel p-6">
                <h3 className="text-lg font-bold mb-4">Evaluated Matches scores</h3>
                <div className="space-y-3">
                  {analytics.match_scores.slice(0, 10).map((score, i) => (
                    <div key={i} className="flex justify-between items-center bg-slate-950/40 border border-slate-850 p-3 rounded-lg">
                      <span className="text-sm font-semibold">Match score #{i+1}</span>
                      <span className={`px-2 py-0.5 rounded font-extrabold text-xs ${
                        score >= 80 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                      }`}>{score}%</span>
                    </div>
                  ))}
                  {analytics.match_scores.length === 0 && (
                    <div className="text-slate-500 py-16 text-center text-sm">No match score lists generated.</div>
                  )}
                </div>
              </div>

              {/* Source Distribution share list */}
              <div className="glass-panel p-6">
                <h3 className="text-lg font-bold mb-4">Discovery Channels Detailed share</h3>
                <div className="space-y-4">
                  {analytics.top_sources.map((src, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-sm mb-1.5 font-medium">
                        <span>{src.source}</span>
                        <span className="text-slate-400">{src.count} listings</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                        <div 
                          className="bg-brand-500 h-full rounded-full" 
                          style={{ width: `${(src.count / (analytics.summary.jobs_found || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 9: EDIT PROFILE */}
        {activeTab === 'profile' && profile && (
          <div className="glass-panel p-8 max-w-3xl mx-auto animate-fade-in">
            <h3 className="text-xl font-bold mb-6 font-display text-white border-b border-slate-800 pb-4">Edit Candidate Profile</h3>
            
            {/* Resume Upload Section */}
            <div className="mb-8 border-b border-slate-800 pb-8">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Resume or CV</h4>
              
              <div 
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('resume-file-input').click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 ${
                  dragActive 
                    ? 'border-brand-500 bg-brand-500/5 shadow-lg shadow-brand-500/10 scale-[1.01]' 
                    : uploadState.status === 'error'
                      ? 'border-rose-500/30 bg-rose-500/5 hover:border-rose-500/50'
                      : uploadState.status === 'success'
                        ? 'border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500/50'
                        : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/10'
                }`}
              >
                <input 
                  id="resume-file-input"
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleResumeUpload(e.target.files[0]);
                    }
                  }}
                />
                
                <div className="flex flex-col items-center justify-center space-y-3">
                  <div className={`p-3 rounded-xl ${
                    uploadState.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                    uploadState.status === 'error' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-900 text-slate-400'
                  }`}>
                    <FileText className="h-6 w-6" />
                  </div>
                  
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {uploadState.status === 'uploading' && "Uploading resume..."}
                      {uploadState.status === 'success' && "Resume uploaded successfully!"}
                      {uploadState.status === 'error' && "Upload failed"}
                      {uploadState.status === 'idle' && (profile.resume_path ? "Replace your Resume / CV" : "Upload your Resume / CV")}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Drag and drop your file here, or click to browse
                    </p>
                  </div>
                  
                  <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                    PDF, DOC, DOCX up to 10MB
                  </div>
                </div>
              </div>

              {/* Show Status or Errors */}
              {uploadState.status === 'error' && (
                <div className="mt-3 flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl font-medium">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {uploadState.error}
                </div>
              )}

              {/* Current Resume details if present */}
              {profile.resume_path && (
                <div className="mt-4 p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                      <Check className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Active Resume</span>
                      <span className="text-xs text-slate-200 block truncate mt-0.5 font-mono">
                        {profile.resume_path.split('/').pop().split('\\').pop()}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 font-extrabold uppercase px-2 py-0.5 rounded">
                    Verified
                  </span>
                </div>
              )}
            </div>

            <form onSubmit={handleUpdateProfile} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Full Name</label>
                  <input 
                    type="text" 
                    required
                    value={profileForm.name}
                    onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Email Address</label>
                  <input 
                    type="email" 
                    required
                    value={profileForm.email}
                    onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Contact Phone</label>
                  <input 
                    type="text" 
                    required
                    value={profileForm.phone}
                    onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">LinkedIn URL</label>
                  <input 
                    type="text" 
                    required
                    value={profileForm.linkedin}
                    onChange={(e) => setProfileForm({ ...profileForm, linkedin: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">GitHub URL</label>
                  <input 
                    type="text" 
                    required
                    value={profileForm.github}
                    onChange={(e) => setProfileForm({ ...profileForm, github: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Portfolio URL</label>
                  <input 
                    type="text" 
                    required
                    value={profileForm.portfolio}
                    onChange={(e) => setProfileForm({ ...profileForm, portfolio: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Skills Inventory (Comma-separated)</label>
                <textarea 
                  required
                  value={profileForm.skills}
                  onChange={(e) => setProfileForm({ ...profileForm, skills: e.target.value })}
                  className="w-full h-24 bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none resize-none leading-relaxed"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Experience Summary</label>
                <input 
                  type="text" 
                  required
                  value={profileForm.experience}
                  onChange={(e) => setProfileForm({ ...profileForm, experience: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-lg p-2.5 text-sm text-slate-200 outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 border-t border-slate-800 pt-6">
                <button 
                  type="submit"
                  className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-lg shadow-md shadow-brand-500/10 transition"
                >
                  Save Profile Changes
                </button>
              </div>
            </form>
          </div>
        )}

      </main>
    </div>
  );
}

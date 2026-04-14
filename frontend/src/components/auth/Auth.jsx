import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Github, AlertCircle, CheckCircle2, BrainCircuit, GraduationCap, BookOpen, Lightbulb } from 'lucide-react';
import { authService } from '../../services/auth.service';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const navigate = useNavigate();

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setErrorMsg("");
    setSuccessMsg("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    const email = e.target.email.value;
    const password = e.target.password.value;
    try{
      let response;
      
      if (isLogin) {
        response = await authService.login(email, password);
      } else {
        const nom = e.target.nom.value;
        const prenom = e.target.prenom.value;
        response = await authService.signup(email, password, nom, prenom);
      }

      const { ok, data } = response;

      if(ok){
        if(isLogin){
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("user", JSON.stringify(data.user));
          navigate(`/Notebooks/${data.user.id}`);   
        }
        else{
          setSuccessMsg(data.message || "Compte créé avec succès ! Connectez-vous.");
          setIsLogin(true);
        }

      }else{
        setErrorMsg(data.message || "Une erreur s'est produite.");
      }
      
    }
    catch(error){
      console.error(error);
      setErrorMsg("Erreur lors de la connexion au serveur. Veuillez réessayer.");
    }
    
  };

  return (
    <div className="min-h-screen bg-background flex relative overflow-hidden">
      {/* Decorative Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] mix-blend-multiply pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-chart-1/20 blur-[120px] mix-blend-multiply pointer-events-none" />
      
      {/* Educational Features Panel */}
      <div className="hidden lg:flex lg:w-1/2 lg:flex-col lg:justify-center lg:items-center relative z-10 p-12 bg-card/10 backdrop-blur-[2px] border-r border-border/50">
        <div className="max-w-lg w-full space-y-8 animate-in fade-in slide-in-from-left-8 duration-700 delay-100">
          <div className="inline-flex p-4 rounded-2xl bg-primary/10 shadow-inner border border-primary/20">
            <BrainCircuit className="h-10 w-10 text-primary" />
          </div>
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl mb-4 leading-tight">
              Unlock Your Learning Potential
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-sm">
              Your AI-powered educational companion. Dive deeply into topics, converse with materials, and master subjects faster.
            </p>
          </div>

          <div className="space-y-6 pt-6 border-t border-border/50">
            <div className="flex group">
              <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-xl bg-primary/10 text-primary border border-primary/20 group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-300">
                <GraduationCap className="h-6 w-6" />
              </div>
              <div className="ml-4 flex flex-col justify-center">
                <h3 className="text-lg font-medium text-foreground">Smarter Progression</h3>
                <p className="mt-1 text-sm text-muted-foreground">Adaptive pathways that evolve with you.</p>
              </div>
            </div>

            <div className="flex group">
              <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-xl bg-orange-500/10 text-orange-500 border border-orange-500/20 group-hover:bg-orange-500 group-hover:text-white transition-colors duration-300">
                <BookOpen className="h-6 w-6" />
              </div>
              <div className="ml-4 flex flex-col justify-center">
                <h3 className="text-lg font-medium text-foreground">Interactive Context</h3>
                <p className="mt-1 text-sm text-muted-foreground">Talk directly to your study guides.</p>
              </div>
            </div>

            <div className="flex group">
              <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-xl bg-green-500/10 text-green-500 border border-green-500/20 group-hover:bg-green-500 group-hover:text-white transition-colors duration-300">
                <Lightbulb className="h-6 w-6" />
              </div>
              <div className="ml-4 flex flex-col justify-center">
                <h3 className="text-lg font-medium text-foreground">Brilliant Insights</h3>
                <p className="mt-1 text-sm text-muted-foreground">Uncover brilliant insights effortlessly.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Auth Form Panel */}
      <div className="flex flex-col justify-center w-full lg:w-1/2 py-12 sm:px-6 lg:px-8 z-10 relative">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground tracking-tight animate-in fade-in slide-in-from-top-4">
            {isLogin ? 'Welcome back, Scholar' : 'Start Your Journey'}
          </h2>
          <p className="mt-2 text-center text-sm text-muted-foreground animate-in fade-in slide-in-from-top-4 delay-75">
            {isLogin ? "Vous n'avez pas de compte? " : "Vous avez déjà un compte? "}
            <button 
              type="button"
              onClick={toggleMode}
              className="font-medium text-primary hover:text-primary/80 transition-colors hover:underline decoration-primary/30 underline-offset-4"
            >
              {isLogin ? 'Créer un compte' : 'Se connecter'}
            </button>
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 transition-all duration-300 transform">
        <div className="bg-card py-8 px-4 shadow-[0_8px_30px_rgb(0,0,0,0.04)] sm:rounded-2xl sm:px-10 border border-border/50 backdrop-blur-xl hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-shadow duration-300">
          
          {errorMsg && (
            <div className="mb-6 flex gap-3 p-4 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-xl animate-in fade-in duration-300">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p>{errorMsg}</p>
            </div>
          )}

          {successMsg && (
            <div className="mb-6 flex gap-3 p-4 text-sm text-green-500 bg-green-500/10 border border-green-500/20 rounded-xl animate-in fade-in duration-300">
              <CheckCircle2 className="h-5 w-5 shrink-0" />
              <p>{successMsg}</p>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="animate-in fade-in slide-in-from-top-4 duration-300">
                <label htmlFor="prenom" className="block text-sm font-medium text-foreground">
                  Prenom
                </label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="prenom"
                    name="prenom"
                    type="text"
                    required={!isLogin}
                    className="block w-full pl-10 pr-3 py-2.5 border border-input rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary bg-background/50 text-foreground sm:text-sm transition-all duration-200 outline-none"
                    placeholder="Entrez votre prenom"
                  />
                </div>
                <br/>
                
                <label htmlFor="nom" className="block text-sm font-medium text-foreground">
                  Nom
                </label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="nom"
                    name="nom"
                    type="text"
                    required={!isLogin}
                    className="block w-full pl-10 pr-3 py-2.5 border border-input rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary bg-background/50 text-foreground sm:text-sm transition-all duration-200 outline-none"
                    placeholder="Entrez votre nom"
                  />
                </div>
                
              </div>
            )}

            <div className="animate-in fade-in duration-300">
              <label htmlFor="email" className="block text-sm font-medium text-foreground">
                Email address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="block w-full pl-10 pr-3 py-2.5 border border-input rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary bg-background/50 text-foreground sm:text-sm transition-all duration-200 outline-none"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            

            <div className="animate-in fade-in duration-300 delay-75">
              <label htmlFor="password" className="block text-sm font-medium text-foreground">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  required
                  className="block w-full pl-10 pr-3 py-2.5 border border-input rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary bg-background/50 text-foreground sm:text-sm transition-all duration-200 outline-none"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {isLogin && (
              <div className="flex items-center justify-between animate-in fade-in duration-300 delay-100">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-primary focus:ring-primary border-input rounded cursor-pointer"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-foreground cursor-pointer">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <a href="#" className="font-medium text-primary hover:text-primary/80 transition-colors">
                    Forgot password?
                  </a>
                </div>
              </div>
            )}

            <div className="animate-in fade-in duration-300 delay-150 relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-chart-1 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
              <button
                type="submit"
                className="relative w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all duration-200 active:scale-[0.98]"
              >
                {isLogin ? 'Sign in' : 'Create account'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      </div>
      
      </div>
    </div>
  );
}

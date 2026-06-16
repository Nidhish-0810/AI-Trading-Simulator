import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, User, Activity, CheckCircle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import toast from 'react-hot-toast';

const PERKS = [
  '$100,000 virtual starting balance',
  'Real-time market data via Yahoo Finance',
  'AI trading signals (RSI, MACD, Bollinger)',
  'Advanced portfolio analytics',
  'Backtesting engine with 4 strategies',
  'Leaderboard & achievements system',
];

export default function Register() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [showPass, setShowPass] = useState(false);
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const e = {};
    if (!form.email.includes('@')) e.email = 'Valid email required';
    if (form.username.length < 3) e.username = 'Min 3 characters';
    if (form.password.length < 8) e.password = 'Min 8 characters';
    if (!/[A-Z]/.test(form.password)) e.password = 'Must include uppercase letter';
    if (!/[0-9]/.test(form.password)) e.password = 'Must include a number';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    try {
      await register(form);
      toast.success('Account created! Welcome to TradeAI 🎉');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed';
      toast.error(msg);
    }
  };

  const field = (name, label, type = 'text', Icon, placeholder) => (
    <div>
      <label className="block text-sm font-medium text-gray-400 mb-2">{label}</label>
      <div className="relative">
        {Icon && <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />}
        <input
          type={name === 'password' ? (showPass ? 'text' : 'password') : type}
          value={form[name]}
          onChange={(e) => setForm({ ...form, [name]: e.target.value })}
          placeholder={placeholder}
          className={`w-full ${Icon ? 'pl-10' : 'pl-4'} ${name === 'password' ? 'pr-12' : 'pr-4'} py-3 rounded-xl bg-white/5 border ${errors[name] ? 'border-red-500' : 'border-white/10'} text-white placeholder-gray-600 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 outline-none transition-all`}
        />
        {name === 'password' && (
          <button type="button" onClick={() => setShowPass(!showPass)}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
            {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {errors[name] && <p className="mt-1 text-xs text-red-400">{errors[name]}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      <div className="hidden lg:flex flex-1 flex-col justify-center px-12 bg-gradient-to-br from-violet-900/10 to-cyan-900/10 border-r border-white/5 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-violet-600/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-0 w-64 h-64 bg-cyan-600/10 rounded-full blur-[80px]" />
        <div className="relative z-10">
          <Link to="/" className="flex items-center gap-2 mb-12">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-black bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
              TradeAI
            </span>
          </Link>
          <h2 className="text-4xl font-black text-white mb-4">Everything Included. Zero Cost.</h2>
          <p className="text-gray-400 mb-10 text-lg">Start trading immediately with your free account.</p>
          <div className="space-y-4">
            {PERKS.map((perk, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-3"
              >
                <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span className="text-gray-300">{perk}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-8 py-12">
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-full max-w-md"
        >
          <div className="lg:hidden mb-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <span className="text-xl font-black bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">TradeAI</span>
            </Link>
          </div>

          <h1 className="text-3xl font-black text-white mb-2">Create your account</h1>
          <p className="text-gray-500 mb-8">Start with $100,000 virtual balance. No credit card needed.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {field('full_name', 'Full Name (Optional)', 'text', User, 'John Doe')}
            {field('username', 'Username', 'text', User, 'trader123')}
            {field('email', 'Email', 'email', Mail, 'trader@example.com')}
            {field('password', 'Password', 'password', Lock, '••••••••')}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-bold text-base transition-all duration-200 shadow-lg shadow-violet-500/20 hover:shadow-violet-500/40 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? 'Creating account...' : 'Create Free Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-gray-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-violet-400 hover:text-violet-300 font-medium">Sign in</Link>
          </p>

          <p className="mt-6 text-center text-xs text-gray-700">
            By creating an account, you agree to our Terms of Service. This is a simulation platform — no real money involved.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
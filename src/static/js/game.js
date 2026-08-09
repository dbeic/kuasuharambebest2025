// PWA Install Button
let deferredPrompt;
const installBtn = document.getElementById('installBtn');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
        installBtn.style.display = 'inline-block';
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                installBtn.style.display = 'none';
                if (typeof unlockAchievement === 'function') {
                    unlockAchievement('app_installer');
                }
            }
            deferredPrompt = null;
        });
    }
});

window.addEventListener('appinstalled', () => {
    if (installBtn) installBtn.style.display = 'none';
    deferredPrompt = null;
    if (typeof unlockAchievement === 'function') {
        unlockAchievement('app_installer');
    }
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(function(registration) {
                console.log('ServiceWorker registered successfully');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}

// Network Status
function updateOnlineStatus() {
    const banner = document.getElementById('offlineBanner');
    const entertainment = document.getElementById('offlineEntertainment');
    if (!navigator.onLine) {
        if (banner) banner.style.display = 'block';
        if (entertainment) entertainment.style.display = 'block';
        if (typeof unlockAchievement === 'function') {
            unlockAchievement('offline_explorer');
        }
    } else {
        if (banner) banner.style.display = 'none';
        if (entertainment) entertainment.style.display = 'none';
    }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
document.addEventListener('DOMContentLoaded', updateOnlineStatus);

// Add global animation styles if not present
(function addGlobalStyles() {
    if (document.getElementById('game-animation-styles')) return;
    const style = document.createElement('style');
    style.id = 'game-animation-styles';
    style.textContent = `
        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(30px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes slideInRight {
            0% { opacity: 0; transform: translateX(50px); }
            100% { opacity: 1; transform: translateX(0); }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
        }
        @keyframes glow {
            0%, 100% { text-shadow: 0 0 20px #FFD70044, 0 0 40px #FFD70022; }
            50% { text-shadow: 0 0 40px #FFD70088, 0 0 80px #FFD70044; }
        }
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes bounceIn {
            0% { transform: scale(0.3); opacity: 0; }
            50% { transform: scale(1.05); opacity: 1; }
            70% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
        @keyframes cardFlip {
            0% { transform: rotateY(0deg); }
            100% { transform: rotateY(360deg); }
        }
        @keyframes rainbow {
            0% { color: #FF6B6B; }
            16% { color: #FFD93D; }
            33% { color: #6BCB77; }
            50% { color: #4D96FF; }
            66% { color: #9B59B6; }
            83% { color: #FF6B6B; }
            100% { color: #FF6B6B; }
        }
        @keyframes confettiFall {
            0% { transform: translateY(0) rotate(0deg) scale(0.8); opacity: 0; }
            10% { opacity: 1; transform: translateY(20px) rotate(30deg) scale(1); }
            100% { transform: translateY(110vh) rotate(720deg) scale(0.3); opacity: 0; }
        }
        .animate-fade-in-up {
            animation: fadeInUp 0.6s ease-out forwards;
            opacity: 0;
        }
        .animate-bounce-in {
            animation: bounceIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
        .result-win {
            border-left: 4px solid #FFD700 !important;
            background: linear-gradient(90deg, rgba(255,215,0,0.08), rgba(255,215,0,0.02)) !important;
            transition: all 0.3s ease;
        }
        .result-win:hover {
            background: linear-gradient(90deg, rgba(255,215,0,0.15), rgba(255,215,0,0.05)) !important;
            transform: scale(1.01);
        }
        .result-jackpot {
            border-left: 4px solid #FF6B35 !important;
            background: linear-gradient(90deg, rgba(255,107,53,0.12), rgba(255,107,53,0.03)) !important;
            animation: glow 1.5s ease-in-out infinite !important;
        }
        .result-loss {
            border-left: 4px solid rgba(255,255,255,0.1);
            opacity: 0.7;
        }
        .live-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #FF4444;
            border-radius: 50%;
            animation: pulse 0.8s ease-in-out infinite;
            margin-left: 8px;
        }
        .game-status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        .status-item {
            background: rgba(255,255,255,0.03);
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .status-item:hover {
            background: rgba(255,255,255,0.06);
            transform: translateY(-2px);
            border-color: rgba(255,215,0,0.15);
        }
        .status-item .label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-item .value {
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .results-scroll {
            max-height: 400px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        .results-scroll::-webkit-scrollbar {
            width: 4px;
        }
        .results-scroll::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
        }
        .results-scroll::-webkit-scrollbar-thumb {
            background: rgba(255,215,0,0.3);
            border-radius: 4px;
        }
        .results-scroll::-webkit-scrollbar-thumb:hover {
            background: rgba(255,215,0,0.5);
        }
        .game-result {
            padding: 12px 16px;
            margin-bottom: 6px;
            border-radius: 8px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            transition: all 0.3s ease;
            animation: fadeInUp 0.4s ease-out forwards;
            opacity: 0;
        }
        .game-result:hover {
            background: rgba(255,255,255,0.04);
            transform: translateX(4px);
            border-color: rgba(255,255,255,0.08);
        }
        .game-result .winner {
            color: #FFD700;
            font-weight: 600;
        }
        .game-result .amount {
            color: #4CAF50;
            font-weight: 600;
        }
        .game-result.jackpot .amount {
            color: #FF6B35;
            animation: glow 1s ease-in-out infinite;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .feature-card {
            background: rgba(255,255,255,0.02);
            padding: 20px 16px;
            border-radius: 14px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.04);
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            cursor: default;
            opacity: 0;
        }
        .feature-card:hover {
            transform: translateY(-6px) scale(1.02);
            background: rgba(255,215,0,0.04);
            border-color: rgba(255,215,0,0.12);
            box-shadow: 0 12px 40px rgba(0,0,0,0.2);
        }
        .feature-card:active {
            transform: scale(0.95);
        }
        .card {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            transition: all 0.3s ease;
        }
        .card:hover {
            border-color: rgba(255,255,255,0.08);
        }
        .btn-primary {
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            overflow: hidden;
        }
        .btn-primary:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 30px rgba(212, 175, 55, 0.3);
        }
        .btn-primary:active {
            transform: scale(0.95);
        }
        .btn-primary::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.05), transparent);
            transform: rotate(45deg) translateX(-100%);
            transition: all 0.6s ease;
        }
        .btn-primary:hover::after {
            transform: rotate(45deg) translateX(100%);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }
        .flash-message {
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 12px;
            animation: slideInRight 0.4s ease-out forwards;
            border-left: 4px solid;
        }
        .flash-message.error {
            background: rgba(244, 67, 54, 0.1);
            border-color: #F44336;
            color: #EF5350;
        }
        .flash-message.success {
            background: rgba(76, 175, 80, 0.1);
            border-color: #4CAF50;
            color: #66BB6A;
        }
        .flash-message.info {
            background: rgba(33, 150, 243, 0.1);
            border-color: #2196F3;
            color: #42A5F5;
        }
        @media (max-width: 600px) {
            .game-effect-text {
                font-size: 1.4rem !important;
                padding: 20px 30px !important;
                min-width: 150px !important;
            }
            .game-status-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
            .status-item .value {
                font-size: 0.95rem;
            }
            .features-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            .feature-card {
                padding: 14px 10px;
            }
            .game-result {
                padding: 10px 12px;
                font-size: 0.85rem;
            }
            .card {
                padding: 14px;
            }
        }
        @media (min-width: 1200px) {
            .game-effect-text {
                font-size: 3rem !important;
                padding: 40px 70px !important;
            }
            .features-grid {
                grid-template-columns: repeat(4, 1fr);
            }
            .game-status-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
    `;
    document.head.appendChild(style);
})();

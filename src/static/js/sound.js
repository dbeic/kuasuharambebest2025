// Sound Manager for Harambee Cash
class SoundManager {
    constructor() {
        this.sounds = {};
        this.enabled = true;
        this.loadSounds();
    }

    loadSounds() {
        const soundFiles = {
            'gameStart': '/static/sounds/game-start.wav',
            'gameEnd': '/static/sounds/game-end.wav',
            'win': '/static/sounds/win.wav',
            'loss': '/static/sounds/loss.wav',
            'deposit': '/static/sounds/deposit.wav',
            'withdraw': '/static/sounds/withdraw.wav',
            'click': '/static/sounds/click.wav',
            'alert': '/static/sounds/alert.wav',
            'jackpot': '/static/sounds/jackpot.wav'
        };

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            this.enabled = false;
            console.log('Web Audio API not supported');
            return;
        }

        for (const [name, url] of Object.entries(soundFiles)) {
            this.loadSound(name, url);
        }
    }

    loadSound(name, url) {
        fetch(url)
            .then(response => response.arrayBuffer())
            .then(arrayBuffer => {
                return this.audioContext.decodeAudioData(arrayBuffer);
            })
            .then(audioBuffer => {
                this.sounds[name] = audioBuffer;
                console.log('✅ Sound loaded:', name);
            })
            .catch(error => {
                console.log('⚠️ Could not load sound:', name, error);
            });
    }

    play(name, volume = 0.7) {
        if (!this.enabled || !this.sounds[name]) return;
        try {
            const source = this.audioContext.createBufferSource();
            const gainNode = this.audioContext.createGain();
            source.buffer = this.sounds[name];
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            gainNode.gain.value = volume;
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
            source.start();
        } catch (e) {
            console.log('Error playing sound:', e);
        }
    }

    playGameStart() { 
        this.play('gameStart', 0.5); 
        this.showGameEffect('🚀 GAME STARTING!', '#FFD700', 'game-start-effect');
    }
    
    playGameEnd() { 
        this.play('gameEnd', 0.7); 
        this.showGameEffect('🏁 GAME COMPLETE!', '#4CAF50', 'game-end-effect');
    }
    
    playWin() { 
        this.play('win', 0.8); 
        this.showGameEffect('🎉 YOU WON! 🎉', '#FFD700', 'win-effect');
        this.createConfetti(60);
        this.createFloatingCoins(20);
    }
    
    playLoss() { 
        this.play('loss', 0.5); 
        this.showGameEffect('💪 BETTER LUCK NEXT TIME!', '#FF6B35', 'loss-effect');
        this.createShakeEffect();
    }
    
    playDeposit() { 
        this.play('deposit', 0.6); 
        this.showGameEffect('💰 DEPOSIT SUCCESSFUL!', '#4CAF50', 'deposit-effect');
        this.createFloatingCoins(15);
        this.createSparkleBurst();
    }
    
    playWithdraw() { 
        this.play('withdraw', 0.6); 
        this.showGameEffect('📤 WITHDRAWAL PROCESSED', '#2196F3', 'withdraw-effect');
        this.createFloatingCoins(10);
    }
    
    playJackpot() { 
        this.play('jackpot', 0.9); 
        this.showGameEffect('🏆 JACKPOT! 🏆', '#FFD700', 'jackpot-effect');
        this.createConfetti(150);
        this.createFloatingCoins(40);
        this.createSparkleBurst();
        this.createJackpotPulse();
    }
    
    playClick() { this.play('click', 0.3); }
    playAlert() { this.play('alert', 0.6); }

    showGameEffect(message, color, effectClass) {
        const existing = document.querySelector('.game-effect-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.className = 'game-effect-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; z-index: 9998;
            background: radial-gradient(circle at center, ${color}22 0%, transparent 70%);
            animation: effectOverlayFade 1.8s ease-out forwards;
        `;
        
        const effect = document.createElement('div');
        effect.className = `game-effect-text ${effectClass || ''}`;
        effect.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0.5);
            background: rgba(0,0,0,0.88); color: ${color}; padding: 30px 55px;
            border-radius: 24px; z-index: 9999; text-align: center;
            border: 3px solid ${color}; font-size: 2.2rem; font-weight: 800;
            box-shadow: 0 0 80px ${color}66, inset 0 0 60px ${color}22;
            pointer-events: none; letter-spacing: 1px;
            animation: effectPopIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            backdrop-filter: blur(8px);
            text-shadow: 0 0 30px ${color}44;
            min-width: 200px;
        `;
        effect.textContent = message;
        
        document.body.appendChild(overlay);
        document.body.appendChild(effect);

        setTimeout(() => {
            effect.style.animation = 'effectPopOut 0.5s ease-in forwards';
            overlay.style.animation = 'effectOverlayFadeOut 0.5s ease-in forwards';
            setTimeout(() => {
                effect.remove();
                overlay.remove();
            }, 500);
        }, 1800);
    }

    createConfetti(count) {
        count = count || 50;
        const colors = ['#FFD700', '#FF6B35', '#4CAF50', '#2196F3', '#FF4081', '#AB47BC', '#FF5722', '#00BCD4', '#E91E63', '#8BC34A'];
        const shapes = ['circle', 'square', 'triangle'];
        const container = document.createElement('div');
        container.className = 'confetti-container';
        container.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; z-index: 10000; overflow: hidden;
        `;
        document.body.appendChild(container);

        for (let i = 0; i < count; i++) {
            const c = document.createElement('div');
            const color = colors[Math.floor(Math.random() * colors.length)];
            const shape = shapes[Math.floor(Math.random() * shapes.length)];
            const size = Math.random() * 10 + 4;
            const startX = Math.random() * window.innerWidth;
            const duration = Math.random() * 2.5 + 1.5;
            const delay = Math.random() * 0.8;
            const rotation = Math.random() * 720;
            const wobble = Math.random() * 100 - 50;
            
            let shapeStyle = '';
            if (shape === 'circle') {
                shapeStyle = `border-radius: 50%; width: ${size}px; height: ${size}px;`;
            } else if (shape === 'square') {
                shapeStyle = `border-radius: 2px; width: ${size}px; height: ${size}px;`;
            } else {
                shapeStyle = `width: 0; height: 0; border-left: ${size/2}px solid transparent; border-right: ${size/2}px solid transparent; border-bottom: ${size}px solid ${color}; background: transparent;`;
            }

            c.style.cssText = `
                position: absolute; left: ${startX}px; top: -30px;
                ${shapeStyle}
                background: ${shape === 'triangle' ? 'transparent' : color};
                transform: rotate(0deg) scale(0.8);
                animation: confettiFall ${duration}s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${delay}s forwards;
                --wobble: ${wobble}px;
                --rot: ${rotation}deg;
                opacity: 0;
            `;
            container.appendChild(c);
        }

        if (!document.getElementById('confetti-style')) {
            const style = document.createElement('style');
            style.id = 'confetti-style';
            style.textContent = `
                @keyframes confettiFall {
                    0% { transform: translateY(0) rotate(0deg) scale(0.8); opacity: 0; }
                    10% { opacity: 1; transform: translateY(20px) rotate(30deg) scale(1); }
                    100% { transform: translateY(${window.innerHeight + 100}px) rotate(var(--rot)) scale(0.3); opacity: 0; }
                }
                @keyframes effectPopIn {
                    0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
                    100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                }
                @keyframes effectPopOut {
                    0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                    100% { transform: translate(-50%, -50%) scale(1.3); opacity: 0; }
                }
                @keyframes effectOverlayFade {
                    0% { opacity: 0; }
                    20% { opacity: 1; }
                    80% { opacity: 1; }
                    100% { opacity: 0; }
                }
                @keyframes effectOverlayFadeOut {
                    0% { opacity: 1; }
                    100% { opacity: 0; }
                }
                @keyframes floatUp {
                    0% { transform: translateY(0) scale(0.5); opacity: 1; }
                    100% { transform: translateY(-150px) scale(1.2); opacity: 0; }
                }
                @keyframes sparkleBurst {
                    0% { transform: scale(0) rotate(0deg); opacity: 1; }
                    100% { transform: scale(2) rotate(180deg); opacity: 0; }
                }
                @keyframes jackpotPulse {
                    0% { transform: scale(1); box-shadow: 0 0 40px #FFD70044; }
                    50% { transform: scale(1.05); box-shadow: 0 0 100px #FFD70088; }
                    100% { transform: scale(1); box-shadow: 0 0 40px #FFD70044; }
                }
                @keyframes shakeEffect {
                    0%, 100% { transform: translateX(0); }
                    10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
                    20%, 40%, 60%, 80% { transform: translateX(10px); }
                }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => container.remove(), 4000);
    }

    createFloatingCoins(count) {
        count = count || 15;
        const container = document.createElement('div');
        container.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; z-index: 9999; overflow: hidden;
        `;
        document.body.appendChild(container);

        for (let i = 0; i < count; i++) {
            const coin = document.createElement('div');
            const size = Math.random() * 20 + 15;
            const startX = Math.random() * window.innerWidth;
            const startY = Math.random() * window.innerHeight;
            const duration = Math.random() * 1.5 + 1;
            const delay = Math.random() * 0.5;
            
            coin.style.cssText = `
                position: absolute; left: ${startX}px; top: ${startY}px;
                width: ${size}px; height: ${size}px;
                background: radial-gradient(circle at 30% 30%, #FFD700, #D4AF37);
                border-radius: 50%;
                border: 2px solid #FFE082;
                box-shadow: 0 0 20px #FFD70044, inset 0 -4px 8px rgba(0,0,0,0.2);
                animation: floatUp ${duration}s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${delay}s forwards;
                opacity: 0;
                font-size: ${size * 0.6}px;
                display: flex; align-items: center; justify-content: center;
                color: #B8860B;
                font-weight: 900;
            `;
            coin.textContent = '₿';
            container.appendChild(coin);
        }

        setTimeout(() => container.remove(), 3000);
    }

    createSparkleBurst() {
        const container = document.createElement('div');
        container.style.cssText = `
            position: fixed; top: 50%; left: 50%;
            pointer-events: none; z-index: 9999;
            transform: translate(-50%, -50%);
        `;
        document.body.appendChild(container);

        const colors = ['#FFD700', '#FF6B35', '#4CAF50', '#2196F3', '#FF4081', '#AB47BC'];
        const numSparkles = 30;

        for (let i = 0; i < numSparkles; i++) {
            const sparkle = document.createElement('div');
            const angle = (i / numSparkles) * Math.PI * 2;
            const distance = Math.random() * 120 + 60;
            const size = Math.random() * 8 + 4;
            const color = colors[Math.floor(Math.random() * colors.length)];
            const duration = Math.random() * 0.6 + 0.4;
            const delay = Math.random() * 0.2;

            sparkle.style.cssText = `
                position: absolute;
                width: ${size}px; height: ${size}px;
                background: ${color};
                border-radius: 50%;
                box-shadow: 0 0 15px ${color}66;
                animation: sparkleBurst ${duration}s ease-out ${delay}s forwards;
                --tx: ${Math.cos(angle) * distance}px;
                --ty: ${Math.sin(angle) * distance}px;
                transform: translate(0, 0) scale(0);
            `;
            container.appendChild(sparkle);
        }

        if (!document.getElementById('sparkle-style')) {
            const style = document.createElement('style');
            style.id = 'sparkle-style';
            style.textContent = `
                @keyframes sparkleBurst {
                    0% { transform: translate(0, 0) scale(0); opacity: 1; }
                    100% { transform: translate(var(--tx), var(--ty)) scale(1.5); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => container.remove(), 1500);
    }

    createJackpotPulse() {
        const pulse = document.createElement('div');
        pulse.style.cssText = `
            position: fixed; top: 50%; left: 50%;
            width: 300px; height: 300px;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle, #FFD70022 0%, transparent 70%);
            pointer-events: none; z-index: 9997;
            animation: jackpotPulse 1.5s ease-in-out 3 forwards;
        `;
        document.body.appendChild(pulse);
        setTimeout(() => pulse.remove(), 4500);
    }

    createShakeEffect() {
        const target = document.querySelector('.game-window') || document.querySelector('.card') || document.body;
        target.style.animation = 'shakeEffect 0.5s ease-in-out';
        setTimeout(() => {
            target.style.animation = '';
        }, 500);
    }
}

window.soundManager = new SoundManager();

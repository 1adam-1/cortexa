import { Link } from 'react-router-dom';
import styles from './Navbar.module.css';
import { Settings, CircleUserRound } from 'lucide-react';
import logoUrl from '../../assets/cortexa.png';

export function Navbar() {
    return (
        <header className={styles.header} role="banner">
            <div className={styles.inner}>

                {/* Logo */}
                <Link to="/" className={styles.brand} aria-label="Go to home">
                    <img src={logoUrl} alt="Company logo" className={styles.logo} />
                </Link>

                {/* Actions */}
                <div className={styles.actions}>
                    <Link
                        to="/settings"
                        className={styles.iconBtn}
                        aria-label="Settings"
                    >
                        <Settings size={20} /> Settings
                    </Link>

                    <Link
                        to="/profile"
                        className={styles.iconBtn}
                        aria-label="Profile"
                    >
                        <CircleUserRound size={20} />
                    </Link>
                </div>

            </div>
        </header>
    );
}
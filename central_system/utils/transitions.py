"""
Window transition effects for ConsultEase.
Provides smooth transitions between windows for a better user experience.
Compatible with Wayland and other window systems that don't support opacity.
"""
import logging
import sys
import os
import platform
import subprocess
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, QRect
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect, QApplication

logger = logging.getLogger(__name__)

class WindowTransitionManager:
    """
    Manages transitions between windows with compatible effects.
    """

    # Default transition settings
    DEFAULT_DURATION = 300
    DEFAULT_TRANSITION_TYPE = "fade"  # Options: "fade", "slide", "none", "zoom"

    # Duration presets based on performance needs
    DURATION_PRESETS = {
        "fast": 150,      # For low-end devices or when performance is critical
        "normal": 300,    # Default balanced setting
        "smooth": 450,    # For high-end devices where smoothness is preferred
    }

    def __init__(self, duration=None, transition_type=None, performance_mode=None):
        """
        Initialize the transition manager.

        Args:
            duration (int, optional): Duration of transitions in milliseconds
            transition_type (str, optional): Type of transition to use ("fade", "slide", "zoom", "none")
            performance_mode (str, optional): Performance preset ("fast", "normal", "smooth")
        """
        # Get performance mode from environment or parameter
        env_performance = os.environ.get("CONSULTEASE_PERFORMANCE_MODE")
        if env_performance and env_performance.lower() in self.DURATION_PRESETS:
            self.performance_mode = env_performance.lower()
            logger.info(f"Using performance mode from environment: {self.performance_mode}")
        elif performance_mode and performance_mode.lower() in self.DURATION_PRESETS:
            self.performance_mode = performance_mode.lower()
        else:
            # Default to normal
            self.performance_mode = "normal"

        # Get duration from environment, parameter, or performance preset
        env_duration = os.environ.get("CONSULTEASE_TRANSITION_DURATION")
        if env_duration and env_duration.isdigit():
            self.duration = int(env_duration)
            logger.info(f"Using transition duration from environment: {self.duration}ms")
        elif duration is not None:
            self.duration = duration
        else:
            # Use duration from performance preset
            self.duration = self.DURATION_PRESETS[self.performance_mode]
            logger.info(f"Using transition duration from performance mode {self.performance_mode}: {self.duration}ms")

        # Get transition type from environment or use default
        env_type = os.environ.get("CONSULTEASE_TRANSITION_TYPE")
        if env_type and env_type.lower() in ["fade", "slide", "none"]:
            self.transition_type = env_type.lower()
            logger.info(f"Using transition type from environment: {self.transition_type}")
        elif transition_type is not None:
            self.transition_type = transition_type
        else:
            self.transition_type = self.DEFAULT_TRANSITION_TYPE

        self.current_animation = None
        self.next_window = None
        self.current_window = None

        # Detect if we're on Wayland or another system with limitations
        self.use_simple_transitions = self._should_use_simple_transitions()
        logger.info(f"Using simple transitions: {self.use_simple_transitions}")

        # If transition type is "none", force simple transitions
        if self.transition_type == "none":
            self.use_simple_transitions = True
            logger.info("Transitions disabled by configuration")

    def _should_use_simple_transitions(self):
        """
        Determine if we should use simple transitions based on platform.
        Enhanced with better platform detection and performance considerations.
        """
        # Check environment variable override (highest priority)
        if "CONSULTEASE_USE_TRANSITIONS" in os.environ:
            use_transitions = os.environ["CONSULTEASE_USE_TRANSITIONS"].lower() == "true"
            use_simple = not use_transitions
            logger.info(f"Using transition setting from environment: {use_transitions}")
            return use_simple

        # Check if we're on Linux and possibly using Wayland
        if sys.platform.startswith('linux'):
            # Check for Wayland environment variables
            for env_var in ['WAYLAND_DISPLAY', 'XDG_SESSION_TYPE']:
                if env_var in os.environ and 'wayland' in os.environ[env_var].lower():
                    logger.info("Detected Wayland session, using simple transitions")
                    return True

            # Check QT_QPA_PLATFORM
            if 'QT_QPA_PLATFORM' in os.environ and 'wayland' in os.environ['QT_QPA_PLATFORM'].lower():
                logger.info("Detected Wayland QPA platform, using simple transitions")
                return True

            # Check for low-end hardware on Linux
            try:
                # Check CPU info
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()

                    # Check for Raspberry Pi
                    if 'raspberry pi' in cpuinfo or 'bcm2708' in cpuinfo or 'bcm2709' in cpuinfo or 'bcm2835' in cpuinfo:
                        logger.info("Detected Raspberry Pi, using simple transitions")
                        return True

                    # Check for low-end CPUs
                    if 'atom' in cpuinfo or 'celeron' in cpuinfo:
                        logger.info("Detected low-end CPU, using simple transitions")
                        return True

                # Check memory (if less than 2GB, use simple transitions)
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    mem_total_line = [line for line in meminfo.split('\n') if 'MemTotal' in line]
                    if mem_total_line:
                        mem_kb = int(mem_total_line[0].split()[1])
                        if mem_kb < 2000000:  # Less than 2GB
                            logger.info(f"Detected low memory ({mem_kb/1000:.0f}MB), using simple transitions")
                            return True
            except Exception as e:
                logger.debug(f"Error checking hardware capabilities: {e}")

            # Check for X11 compositor
            try:
                result = subprocess.run(['xprop', '-root', '_NET_SUPPORTING_WM_CHECK'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    # We have a compositor, should be safe to use advanced transitions
                    logger.info("Detected X11 with compositor, using advanced transitions")
                    return False
            except:
                # If xprop fails, we can't determine compositor status
                pass

        # Check if we're on Windows
        if sys.platform.startswith('win'):
            # Check Windows version
            try:
                win_ver = sys.getwindowsversion()
                # Windows 10 or higher should support transitions well
                if win_ver.major >= 10:
                    logger.info(f"Detected Windows {win_ver.major}.{win_ver.minor}, using advanced transitions")
                    return False
                else:
                    logger.info(f"Detected older Windows {win_ver.major}.{win_ver.minor}, using simple transitions")
                    return True
            except:
                # If we can't determine Windows version, assume it's modern enough
                logger.info("Detected Windows platform, using advanced transitions")
                return False

        # Check if we're on macOS
        if sys.platform.startswith('darwin'):
            # macOS generally supports opacity animations well
            logger.info("Detected macOS platform, using advanced transitions")
            return False

        # Check for mobile platforms
        if hasattr(sys, 'platform'):
            if 'android' in sys.platform or 'ios' in sys.platform:
                logger.info(f"Detected mobile platform {sys.platform}, using simple transitions")
                return True

        # Default to simple transitions for safety on unknown platforms
        logger.info("Unknown platform, defaulting to simple transitions for safety")
        return True

    def fade_out_in(self, current_window, next_window, on_finished=None):
        """
        Perform a transition from current window to next window.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        logger.info(f"Starting transition from {current_window.__class__.__name__} to {next_window.__class__.__name__}")

        self.current_window = current_window
        self.next_window = next_window

        # If transitions are disabled, just switch windows immediately
        if self.transition_type == "none":
            current_window.hide()
            next_window.show()
            next_window.raise_()
            if on_finished:
                on_finished()
            return

        # Always ensure next window is ready to be shown but initially invisible
        if not self.use_simple_transitions:
            next_window.setWindowOpacity(0.0)
        next_window.show()
        next_window.raise_()  # Ensure it's on top

        # Set a failsafe timer to ensure transition completes
        QTimer.singleShot(self.duration * 2, lambda: self._ensure_transition_completed(next_window))

        # Choose transition based on configuration
        if self.use_simple_transitions:
            if self.transition_type == "slide":
                self._perform_slide_transition(current_window, next_window, on_finished)
            else:
                # Default to simple show/hide for other types when simple transitions are forced
                self._perform_simple_transition(current_window, next_window, on_finished)
        else:
            if self.transition_type == "fade":
                self._perform_fade_transition(current_window, next_window, on_finished)
            elif self.transition_type == "slide":
                self._perform_slide_transition(current_window, next_window, on_finished)
            elif self.transition_type == "zoom":
                self._perform_zoom_transition(current_window, next_window, on_finished)
            else:
                # Default to fade for unknown types
                self._perform_fade_transition(current_window, next_window, on_finished)

    def _perform_simple_transition(self, current_window, next_window, on_finished=None):
        """
        Perform a simple show/hide transition without animations.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Simple show/hide with a small delay
            QTimer.singleShot(50, lambda: current_window.hide())

            # Call on_finished after a short delay
            if on_finished:
                QTimer.singleShot(100, on_finished)
        except Exception as e:
            logger.error(f"Simple transition failed: {e}")
            # Immediate fallback
            current_window.hide()
            if on_finished:
                on_finished()

    def _perform_slide_transition(self, current_window, next_window, on_finished=None):
        """
        Perform a slide transition between windows.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Get the screen geometry
            screen_width = current_window.width()

            # Position the next window off-screen to the right
            next_window_pos = next_window.pos()
            next_window.move(screen_width, next_window_pos.y())

            # Create animation to slide in the next window
            slide_in = QPropertyAnimation(next_window, b"pos")
            slide_in.setDuration(self.duration)
            slide_in.setStartValue(next_window.pos())
            slide_in.setEndValue(next_window_pos)
            slide_in.setEasingCurve(QEasingCurve.OutCubic)

            # Start the animation
            slide_in.start()

            # Hide the current window after a short delay
            QTimer.singleShot(int(self.duration * 0.5), lambda: current_window.hide())

            # Call on_finished after transition duration
            if on_finished:
                QTimer.singleShot(self.duration, on_finished)
        except Exception as e:
            logger.warning(f"Slide animation failed, using simple transition: {e}")
            # Fall back to very simple transition
            self._perform_simple_transition(current_window, next_window, on_finished)

    def _perform_zoom_transition(self, current_window, next_window, on_finished=None):
        """
        Perform a zoom transition between windows.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Store original geometry of next window
            original_geometry = next_window.geometry()

            # Start with a smaller size centered in the same position
            center_x = original_geometry.x() + original_geometry.width() / 2
            center_y = original_geometry.y() + original_geometry.height() / 2

            # Calculate starting size (80% of original)
            start_width = int(original_geometry.width() * 0.8)
            start_height = int(original_geometry.height() * 0.8)

            # Calculate starting position to keep centered
            start_x = int(center_x - start_width / 2)
            start_y = int(center_y - start_height / 2)

            # Set initial geometry
            next_window.setGeometry(start_x, start_y, start_width, start_height)

            # Create animation for size
            zoom_anim = QPropertyAnimation(next_window, b"geometry")
            zoom_anim.setDuration(self.duration)
            zoom_anim.setStartValue(next_window.geometry())
            zoom_anim.setEndValue(original_geometry)
            zoom_anim.setEasingCurve(QEasingCurve.OutCubic)

            # Also fade in for a smoother effect
            opacity_effect = QGraphicsOpacityEffect(next_window)
            next_window.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0.5)

            fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
            fade_anim.setDuration(self.duration)
            fade_anim.setStartValue(0.5)
            fade_anim.setEndValue(1.0)
            fade_anim.setEasingCurve(QEasingCurve.OutCubic)

            # Hide current window after a short delay
            QTimer.singleShot(int(self.duration * 0.2), lambda: current_window.hide())

            # When animations complete, clean up
            def on_animation_finished():
                next_window.setGraphicsEffect(None)  # Remove the opacity effect
                if on_finished:
                    on_finished()

            zoom_anim.finished.connect(on_animation_finished)

            # Start animations
            zoom_anim.start()
            fade_anim.start()

        except Exception as e:
            logger.warning(f"Zoom animation failed, falling back to simple transition: {e}")
            # Fall back to simple transition
            self._perform_simple_transition(current_window, next_window, on_finished)

    def _perform_fade_transition(self, current_window, next_window, on_finished=None):
        """
        Perform a fade transition between windows.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Try opacity-based transition with cross-fade
            # Create fade out animation for current window
            fade_out = QPropertyAnimation(current_window, b"windowOpacity")
            fade_out.setDuration(int(self.duration * 1.2))  # Slightly longer for overlap
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.OutCubic)

            # Create fade in animation for next window
            fade_in = QPropertyAnimation(next_window, b"windowOpacity")
            fade_in.setDuration(self.duration)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InCubic)

            # Start fade in after a short delay for cross-fade effect
            QTimer.singleShot(int(self.duration * 0.3), fade_in.start)

            # When fade out completes, hide the window
            def on_fade_out_finished():
                current_window.hide()
                current_window.setWindowOpacity(1.0)  # Reset for future use

                # Call on_finished when both animations are done
                if on_finished and fade_in.state() == QPropertyAnimation.Stopped:
                    on_finished()

            # When fade in completes, call on_finished if fade_out is done
            def on_fade_in_finished():
                if on_finished and fade_out.state() == QPropertyAnimation.Stopped:
                    on_finished()

            fade_out.finished.connect(on_fade_out_finished)
            fade_in.finished.connect(on_fade_in_finished)

            # Start the fade out animation
            self.current_animation = fade_out
            fade_out.start()
        except Exception as e:
            logger.warning(f"Opacity animation failed, falling back to simple transition: {e}")
            # Fall back to simple transition
            self._perform_simple_transition(current_window, next_window, on_finished)

    def _start_fade_in(self, on_finished=None):
        """
        Start the fade in animation for the next window.

        Args:
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Hide the previous window
            if self.current_window:
                self.current_window.hide()
                # Reset opacity for future use
                self.current_window.setWindowOpacity(1.0)

            # Create fade in animation for next window
            fade_in = QPropertyAnimation(self.next_window, b"windowOpacity")
            fade_in.setDuration(self.duration)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InCubic)

            # Connect finished signal
            if on_finished:
                fade_in.finished.connect(on_finished)

            # Start the animation
            self.current_animation = fade_in
            fade_in.start()
        except Exception as e:
            logger.warning(f"Fade in animation failed: {e}")
            # Ensure window is visible
            self.next_window.setWindowOpacity(1.0)
            if on_finished:
                on_finished()

    def fade_in(self, window, on_finished=None):
        """
        Perform a fade in effect on a window.

        Args:
            window (QWidget): The window to fade in
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading in {window.__class__.__name__}")

        # If transitions are disabled, just show the window immediately
        if self.transition_type == "none":
            window.show()
            if on_finished:
                on_finished()
            return

        # Choose transition based on configuration
        if self.use_simple_transitions or self.transition_type != "fade":
            # Simple show for non-fade transitions or when simple transitions are forced
            window.show()
            if on_finished:
                QTimer.singleShot(self.duration, on_finished)
        else:
            try:
                # Prepare window
                window.setWindowOpacity(0.0)
                window.show()

                # Create fade in animation
                fade_in = QPropertyAnimation(window, b"windowOpacity")
                fade_in.setDuration(self.duration)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.InCubic)

                # Connect finished signal
                if on_finished:
                    fade_in.finished.connect(on_finished)

                # Start the animation
                self.current_animation = fade_in
                fade_in.start()
            except Exception as e:
                logger.warning(f"Fade in animation failed, using simple show: {e}")
                window.show()
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)

    def fade_out(self, window, on_finished=None):
        """
        Perform a fade out effect on a window.

        Args:
            window (QWidget): The window to fade out
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading out {window.__class__.__name__}")

        # If transitions are disabled, just hide the window immediately
        if self.transition_type == "none":
            window.hide()
            if on_finished:
                on_finished()
            return

        # Choose transition based on configuration
        if self.use_simple_transitions or self.transition_type != "fade":
            # Simple hide for non-fade transitions or when simple transitions are forced
            window.hide()
            if on_finished:
                QTimer.singleShot(self.duration, on_finished)
        else:
            try:
                # Create fade out animation
                fade_out = QPropertyAnimation(window, b"windowOpacity")
                fade_out.setDuration(self.duration)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.OutCubic)

                # When fade out completes, hide the window and reset opacity
                def on_fade_out_finished():
                    window.hide()
                    window.setWindowOpacity(1.0)
                    if on_finished:
                        on_finished()

                fade_out.finished.connect(on_fade_out_finished)

                # Start the animation
                self.current_animation = fade_out
                fade_out.start()
            except Exception as e:
                logger.warning(f"Fade out animation failed, using simple hide: {e}")
                window.hide()
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)

    def _ensure_transition_completed(self, next_window):
        """
        Failsafe method to ensure transition completes properly.
        This is called after a timeout to make sure the window is visible.

        Args:
            next_window (QWidget): The window that should be visible after transition
        """
        if next_window:
            # Check if window is visible and has proper opacity
            if not next_window.isVisible():
                logger.warning("Transition failsafe: Window not visible, forcing visibility")
                next_window.show()
                next_window.raise_()
                next_window.activateWindow()

            # Ensure opacity is set to 1.0 (fully visible)
            if hasattr(next_window, 'windowOpacity') and next_window.windowOpacity() < 1.0:
                logger.warning("Transition failsafe: Window opacity not 1.0, resetting")
                next_window.setWindowOpacity(1.0)

            # If current_window is still visible, hide it
            if self.current_window and self.current_window.isVisible():
                logger.warning("Transition failsafe: Previous window still visible, hiding")
                self.current_window.hide()

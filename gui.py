"""JarMug v0.1 Windows desktop entry point."""

import os
import time
from tkinter import messagebox

import customtkinter as ctk

from core.generation import OUTPUT_DIR
from core.jobs import GenerationJob
from core.library import recent_wavs
from core.playback import WavPlayer, wav_duration

BG = "#171411"
PANEL = "#24201B"
FIELD = "#1C1915"
GOLD = "#D4AD69"
GOLD_HOVER = "#BB9253"
TEXT = "#F3EBDD"
MUTED = "#B4A897"


class JarMugApp(ctk.CTk):
    def __init__(self, job=None, player=None):
        super().__init__()
        self.job = job if job is not None else GenerationJob()
        self.player = player if player is not None else WavPlayer()
        self.output_path = None
        self.output_duration = None
        self.playing = False
        self.started_at = 0.0
        self.generation_detail = "Starting Stable Audio…"
        self.title("JarMug • Local audio studio")
        self.geometry("660x790")
        self.minsize(600, 700)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._close)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(24, 18), sticky="ew")
        ctk.CTkLabel(header, text="JarMug", font=("Segoe UI", 32, "bold"),
                     text_color=GOLD).pack(anchor="w")
        ctk.CTkLabel(header, text="Just a Rather Music Generator",
                     font=("Segoe UI", 13), text_color=MUTED).pack(anchor="w")
        ctk.CTkLabel(header, text="LOCAL AUDIO STUDIO  /  v0.1", font=("Segoe UI", 10),
                     text_color=MUTED).pack(anchor="w", pady=(8, 0))

        self.content = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        card = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=16)
        card.grid(row=0, column=0, padx=18, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)
        self.mode = ctk.CTkSegmentedButton(
            card, values=["Music", "Instrument", "SFX"], height=36,
            selected_color="#725733", selected_hover_color="#87683D",
            unselected_color=FIELD, unselected_hover_color="#383026",
            text_color=TEXT, command=self._mode_changed)
        self.mode.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="ew")
        self.mode.set("Music")
        self.hint = ctk.CTkLabel(card, text="Full musical scenes, moods, and arrangements.",
                                text_color=MUTED, anchor="w", font=("Segoe UI", 12))
        self.hint.grid(row=1, column=0, padx=20, sticky="ew")
        ctk.CTkLabel(card, text="What would you like to hear?", text_color=TEXT,
                     font=("Segoe UI", 14, "bold"), anchor="w").grid(
                         row=2, column=0, padx=20, pady=(18, 8), sticky="ew")
        self.prompt = ctk.CTkTextbox(card, height=155, fg_color=FIELD,
                                     text_color=TEXT, border_width=1,
                                     border_color="#4A3E2D", corner_radius=10,
                                     font=("Segoe UI", 14), wrap="word")
        self.prompt.grid(row=3, column=0, padx=20, sticky="nsew")
        ctk.CTkLabel(card, text="DURATION", text_color=MUTED,
                     font=("Segoe UI", 11), anchor="w").grid(
                         row=4, column=0, padx=20, pady=(16, 6), sticky="ew")
        self.duration = ctk.CTkSegmentedButton(
            card, values=["10s", "30s", "60s", "120s"], height=32,
            selected_color="#725733", selected_hover_color="#87683D",
            unselected_color=FIELD, unselected_hover_color="#383026", text_color=TEXT)
        self.duration.grid(row=5, column=0, padx=20, sticky="ew")
        self.duration.set("10s")
        self.generate_button = ctk.CTkButton(
            card, text="Generate audio", height=44, fg_color=GOLD,
            hover_color=GOLD_HOVER, text_color=BG, text_color_disabled=MUTED,
            font=("Segoe UI", 15, "bold"), command=self._generate)
        self.generate_button.grid(row=6, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.progress = ctk.CTkProgressBar(card, height=3, progress_color=GOLD,
                                           fg_color=FIELD, mode="indeterminate")
        self.progress.grid(row=7, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.progress.set(0)
        self.status = ctk.CTkLabel(card, text="Ready when you are.", text_color=MUTED,
                                   anchor="w", justify="left", wraplength=520,
                                   font=("Segoe UI", 12))
        self.status.grid(row=8, column=0, padx=20, pady=(0, 16), sticky="ew")

        footer = ctk.CTkFrame(self.content, fg_color="transparent")
        footer.grid(row=1, column=0, padx=22, pady=(16, 20), sticky="ew")
        footer.grid_columnconfigure(2, weight=1)
        self.file_label = ctk.CTkLabel(footer, text="Your generated WAV will appear here.",
                                       text_color=MUTED, anchor="w", wraplength=550,
                                       font=("Segoe UI", 11))
        self.file_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.timeline = ctk.CTkProgressBar(footer, height=5, fg_color=FIELD,
                                           progress_color=GOLD)
        self.timeline.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.timeline.set(0)
        self.timeline_label = ctk.CTkLabel(footer, text="0:00 / --:--",
                                            text_color=MUTED, anchor="e",
                                            font=("Segoe UI", 11))
        self.timeline_label.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 10))
        self.play_button = ctk.CTkButton(footer, text="Play", width=80, state="disabled",
                                         fg_color="#59452D", hover_color="#725733",
                                         command=self._play)
        self.play_button.grid(row=3, column=0, padx=(0, 8))
        self.stop_button = ctk.CTkButton(footer, text="Stop", width=80, state="disabled",
                                         fg_color="#39312A", hover_color="#4A4036",
                                         command=self._stop)
        self.stop_button.grid(row=3, column=1)
        ctk.CTkButton(footer, text="Open Output Folder", width=160,
                      fg_color="#39312A", hover_color="#4A4036",
                      command=self._open_output).grid(row=3, column=2, sticky="e")
        recent = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=14)
        recent.grid(row=2, column=0, padx=18, pady=(0, 20), sticky="ew")
        recent.grid_columnconfigure(0, weight=1)
        recent_header = ctk.CTkFrame(recent, fg_color="transparent")
        recent_header.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")
        ctk.CTkLabel(recent_header, text="Recent generations", text_color=TEXT,
                     font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkButton(recent_header, text="Refresh", width=62, height=24,
                      fg_color="#39312A", hover_color="#4A4036",
                      command=self._refresh_recent).pack(side="right")
        self.recent_list = ctk.CTkScrollableFrame(recent, height=106, fg_color=FIELD,
                                                   corner_radius=8)
        self.recent_list.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
        self.recent_list.grid_columnconfigure(0, weight=1)
        self.recent_buttons = []
        self._refresh_recent()
        self._poll_id = self.after(100, self._poll)

    @staticmethod
    def _clock(seconds):
        whole = max(0, int(seconds))
        return f"{whole // 60}:{whole % 60:02d}"

    def _update_timeline(self, position=0.0):
        duration = self.output_duration
        self.timeline.set(min(1.0, max(0.0, position / duration)) if duration else 0)
        self.timeline_label.configure(
            text=f"{self._clock(position)} / {self._clock(duration) if duration is not None else '--:--'}")

    def _select_output(self, path):
        if self.playing:
            self._stop()
        self.output_path = path
        self.output_duration = wav_duration(path)
        length = self._clock(self.output_duration) if self.output_duration is not None else "duration unknown"
        self.file_label.configure(text=f"{path.name}  •  {length}")
        self._update_timeline()
        self.play_button.configure(state="disabled" if self.job.busy else "normal")

    def _refresh_recent(self):
        for child in self.recent_list.winfo_children():
            child.destroy()
        self.recent_buttons = []
        items = recent_wavs(OUTPUT_DIR)
        if not items:
            ctk.CTkLabel(self.recent_list, text="No WAV files in the output folder yet.",
                         text_color=MUTED, anchor="w").grid(row=0, column=0, sticky="ew")
            return
        for index, item in enumerate(items):
            length = self._clock(item.duration) if item.duration is not None else "--:--"
            button = ctk.CTkButton(
                self.recent_list, text=f"{item.path.name}   •   {length}",
                height=30, anchor="w", fg_color="transparent", hover_color="#383026",
                text_color=TEXT, command=lambda path=item.path: self._select_output(path))
            button.grid(row=index, column=0, pady=1, sticky="ew")
            self.recent_buttons.append(button)

    def _mode_changed(self, mode):
        hints = {"Music": "Full musical scenes, moods, and arrangements.",
                 "Instrument": "A solo instrument, without backing or vocals.",
                 "SFX": "Sound effects and textures, without music."}
        self.hint.configure(text=hints[mode])

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for widget in (self.generate_button, self.mode, self.duration, self.prompt):
            widget.configure(state=state)
        self.generate_button.configure(text="Generating…" if busy else "Generate audio")
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)
        self.play_button.configure(state="normal" if self.output_path and not busy else "disabled")

    def _generate(self):
        if self.job.busy:
            return
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            self.status.configure(text="Describe the audio you want to generate.")
            self.prompt.focus_set()
            return
        self._stop()
        try:
            if self.job.start(self.mode.get().lower(), prompt, int(self.duration.get()[:-1])):
                self.started_at = time.monotonic()
                self.generation_detail = "Starting Stable Audio…"
                self._set_busy(True)
                self.status.configure(text="Starting Stable Audio…  Elapsed 0:00")
        except Exception as error:
            self._set_busy(False)
            self._error("Could not start generation", str(error))

    def _poll(self):
        for kind, value in self.job.poll():
            if kind == "status":
                self.generation_detail = value
            elif kind == "done":
                self._select_output(value)
                self._refresh_recent()
                self._set_busy(False)
                elapsed = self._clock(time.monotonic() - self.started_at)
                self.status.configure(text=f"Generation complete in {elapsed}. WAV saved in the output folder.")
            elif kind == "error":
                self._set_busy(False)
                elapsed = self._clock(time.monotonic() - self.started_at)
                self._error("Generation failed", value)
                self.status.configure(text=f"Generation failed after {elapsed}. {value.splitlines()[0]}")
        if self.job.busy:
            elapsed = int(time.monotonic() - self.started_at)
            self.generate_button.configure(text=f"Generating…  {elapsed // 60}:{elapsed % 60:02d}")
            self.status.configure(text=f"{self.generation_detail}  Elapsed {self._clock(elapsed)}")
        if self.playing:
            try:
                if not self.player.is_playing():
                    self._stop()
                else:
                    self._update_timeline(self.player.position())
            except Exception as error:
                self._audio_error(error)
        self._poll_id = self.after(100, self._poll)

    def _error(self, title, details):
        self.status.configure(text=f"{title}. See details and try again.")
        messagebox.showerror(title, details, parent=self)

    def _audio_error(self, error):
        self.playing = False
        self.stop_button.configure(state="disabled")
        try:
            self.player.close()
        except Exception:
            pass
        self._error("Playback unavailable", f"Check your audio output device. The WAV remains saved.\n\n{error}")

    def _play(self):
        if not self.output_path or self.job.busy:
            return
        try:
            self.player.play(self.output_path)
            self.playing = True
            self._update_timeline()
            self.stop_button.configure(state="normal")
            self.status.configure(text="Playing your latest generation.")
        except Exception as error:
            self._audio_error(error)

    def _stop(self):
        try:
            self.player.stop()
            if self.playing:
                self.status.configure(text="Playback stopped. Ready to play again.")
            self.playing = False
            self._update_timeline()
            self.stop_button.configure(state="disabled")
        except Exception as error:
            self._audio_error(error)

    def _open_output(self):
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            os.startfile(str(OUTPUT_DIR))
        except Exception as error:
            self._error("Could not open output folder", str(error))

    def _close(self):
        if self.job.busy:
            messagebox.showinfo("Generation in progress",
                                "Please wait for generation to finish before closing JarMug.", parent=self)
            return
        try:
            self.player.close()
        finally:
            self.after_cancel(self._poll_id)
            self.destroy()


def main():
    ctk.set_appearance_mode("dark")
    JarMugApp().mainloop()


if __name__ == "__main__":
    main()

import reflex as rx
import httpx

class State(rx.State):
    chat_history: list[dict[str, str]] = []
    current_question: str = ""
    is_working: bool = False
    indexed_papers: list[str] = []

    # Manual setter to fix the DeprecationWarning for Reflex 0.9.0+
    def set_current_question(self, val: str):
        self.current_question = val
    async def handle_upload(self, files: list[rx.UploadFile]):
        upload_success = False
        for file in files:
            upload_data = await file.read()
            async with httpx.AsyncClient() as client:
                try:
                    # Double check this address matches your Backend terminal!
                    response = await client.post(
                        "http://127.0.0.1:8888/upload",
                        files={"file": (file.filename, upload_data, "application/pdf")},
                        timeout=300.0
                    )
                    
                    if response.status_code == 200:
                        if file.filename not in self.indexed_papers:
                            self.indexed_papers.append(file.filename)
                        upload_success = True
                    else:
                        return rx.window_alert(f"Backend Error: {response.text}")

                except Exception as e:
                    # This is where your "Connection Error" is caught
                    return rx.window_alert(f"Connection Error: {str(e)}. Is the Backend running on Port 8888?")
        
        if upload_success:
            return rx.window_alert("Paper Uploaded and Indexed!")

    async def ask_ai(self):
        if not self.current_question:
            return
        
        self.is_working = True
        # Add user message to UI immediately
        self.chat_history.append({"role": "user", "content": self.current_question})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://127.0.0.1:8888/chat",
                    json={"query": self.current_question},
                    timeout=180.0 
                )
                
                if response.status_code == 200:
                    answer = response.json().get("answer")
                    self.chat_history.append({"role": "assistant", "content": str(answer)})
                else:
                    self.chat_history.append({"role": "assistant", "content": f"Backend Error: {response.status_code}"})
            except Exception as e:
                self.chat_history.append({"role": "assistant", "content": f"Connection Error: {str(e)}"})
        
        self.current_question = ""
        self.is_working = False
        
def index() -> rx.Component:
    return rx.flex(
        # --- SIDEBAR ---
        rx.flex(
            rx.heading("AI Research", size="6", color="white", margin_bottom="1em"),
            rx.upload(
                rx.text("Drag PDF here or click to select", color="gray", font_size="0.8em"),
                id="pdf_upload",
                border="1px dashed #444",
                padding="2em",
                border_radius="10px",
            ),
            rx.button(
                "Upload Paper",
                on_click=State.handle_upload(rx.upload_files(upload_id="pdf_upload")),
                margin_top="1em",
                width="100%",
                color_scheme="blue",
            ),
            rx.divider(margin_y="1em"),
            rx.text("Library", font_weight="bold", color="gray", margin_bottom="0.5em"),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        State.indexed_papers, 
                        lambda p: rx.badge(
                            f"📄 {p}", 
                            variant="soft", 
                            color_scheme="blue",
                            width="100%"
                        )
                    ),
                    align_items="start",
                    spacing="2",
                    width="100%",
                ),
                height="50vh",
            ),
            direction="column",
            width="280px",
            height="100vh",
            bg="#111", # Sidebar background
            padding="2em",
            border_right="1px solid #222",
        ),

        # --- MAIN CHAT AREA ---
        rx.flex(
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        State.chat_history,
                        lambda msg: rx.flex(
                            rx.box(
                                rx.markdown(msg["content"]),
                                padding="1em",
                                border_radius="15px",
                                bg=rx.cond(msg["role"] == "user", "#007AFF", "#222"),
                                color="white",
                                max_width="70%",
                            ),
                            justify=rx.cond(msg["role"] == "user", "end", "start"),
                            width="100%",
                            margin_y="0.5em",
                        )
                    ),
                    rx.cond(
                        State.is_working,
                        rx.flex(
                            rx.spinner(size="1", margin_right="0.5em"),
                            rx.text("AI is reading...", font_size="0.8em", color="gray"),
                            align_items="center",
                            padding="1em",
                        )
                    ),
                    width="100%",
                    padding="2em",
                ),
                height="85vh",
            ),

            # --- INPUT BOX ---
            rx.flex(
                rx.input(
                    placeholder="Ask about your research...",
                    value=State.current_question,
                    on_change=State.set_current_question,
                    width="100%",
                    variant="soft",
                    bg="#1A1A1A",
                    border="none",
                    on_key_down=lambda e: rx.cond(e == "Enter", State.ask_ai, None), 
                ),
                rx.button(
                    rx.icon("send"), 
                    on_click=State.ask_ai, 
                    loading=State.is_working,
                    color_scheme="blue",
                ),
                padding="1.5em",
                bg="#111",
                width="100%",
                gap="3",
                border_top="1px solid #222",
            ),
            direction="column",
            flex="1",
            bg="#080808",
        ),
        direction="row",
        width="100%",
        height="100vh",
    )

app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(index)
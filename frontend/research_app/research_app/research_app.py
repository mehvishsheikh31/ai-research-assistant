import reflex as rx
import httpx

class State(rx.State):
    chat_history: list[dict[str, str]] = []
    current_question: str = ""
    is_working: bool = False
    indexed_papers: list[str] = []

    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = await file.read()
            async with httpx.AsyncClient() as client:
                try:
                    # UPDATED: Using Port 8888 and 127.0.0.1 for stability
                    response = await client.post(
                        "http://127.0.0.1:8888/upload",
                        files={"file": (file.filename, upload_data, "application/pdf")},
                        timeout=300.0 # High timeout for PDF processing
                    )
                    if response.status_code == 200:
                        self.indexed_papers.append(file.filename)
                except Exception as e:
                    return rx.window_alert(f"Upload Error: {str(e)}")
                    
        return rx.window_alert("Paper Uploaded and Indexed!")

    async def ask_ai(self):
        if not self.current_question:
            return
        
        self.is_working = True
        # Add user message to UI immediately
        self.chat_history.append({"role": "user", "content": self.current_question})
        
        async with httpx.AsyncClient() as client:
            try:
                # UPDATED: Using Port 8888 and 127.0.0.1
                response = await client.post(
                    "http://127.0.0.1:8888/chat",
                    json={"query": self.current_question},
                    timeout=180.0 # High timeout for AI thinking
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
            ),
            rx.button(
                "Upload Paper",
                on_click=State.handle_upload(rx.upload_files(upload_id="pdf_upload")),
                margin_top="1em",
                color_scheme="blue",
            ),
            rx.divider(margin_y="1em"),
            rx.text("Library", font_weight="bold", color="gray"),
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(State.indexed_papers, lambda p: rx.text(f"📄 {p}", font_size="0.8em")),
                    align_items="start",
                ),
                height="50vh",
            ),
            direction="column",
            width="250px",
            height="100vh",
            bg="#111",
            padding="2em",
        ),
        # --- CHAT AREA ---
        rx.flex(
            rx.scroll_area(
                rx.flex(
                    rx.foreach(
                        State.chat_history,
                        lambda msg: rx.box(
                            rx.markdown(msg["content"]),
                            bg=rx.cond(msg["role"] == "user", "#2D2D2D", "#1A1A1A"),
                            padding="1em",
                            border_radius="10px",
                            margin_y="0.5em",
                            width="fit-content",
                            max_width="80%",
                            align_self=rx.cond(msg["role"] == "user", "end", "start"),
                        )
                    ),
                    direction="column",
                    width="100%",
                ),
                height="85vh",
                width="100%",
                padding="2em",
            ),
            rx.flex(
                rx.input(
                    placeholder="Ask about your research...",
                    value=State.current_question,
                    on_change=State.set_current_question,
                    width="100%",
                ),
                rx.button(
                    "Ask", 
                    on_click=State.ask_ai, 
                    loading=State.is_working,
                    color_scheme="blue",
                ),
                padding="1em",
                bg="#111",
                width="100%",
                gap="2",
            ),
            direction="column",
            flex="1",
            bg="#000",
        ),
        direction="row",
        width="100%",
    )

app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(index)
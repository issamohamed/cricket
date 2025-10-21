import tkinter as tk
from tkinter import font as tkfont
import asyncio
from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import threading
import time
import os

load_dotenv()


class MacTerminalUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Hop Monitor")
        self.root.overrideredirect(False)

        # Set transparency
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='black')

        # Terminal-like dimensions
        window_width = 700
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # Main container
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Terminal font
        self.terminal_font = tkfont.Font(family='Monaco', size=11)
        self.small_font = tkfont.Font(family='Monaco', size=9)

        # Input section
        self.create_input_section(main_frame)

        # Canvas container with scrollbar
        canvas_container = tk.Frame(main_frame, bg='black')
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Scrollbar
        scrollbar = tk.Scrollbar(canvas_container, bg='#333333', troughcolor='black',
                                 activebackground='#00ff00')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Visualization canvas
        self.canvas = tk.Canvas(canvas_container, bg='black', highlightthickness=0,
                                yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Status/Result section
        self.create_result_section(main_frame)

        # Node tracking
        self.nodes = []
        self.node_positions = {}
        self.current_step = 0

    def create_input_section(self, parent):
        input_frame = tk.Frame(parent, bg='black')
        input_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        prompt_label = tk.Label(input_frame, text='your inquiry: ',
                                fg='#00ff00', bg='black',
                                font=self.terminal_font)
        prompt_label.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(input_frame, bg='black', fg='#00ff00',
                                    font=self.terminal_font, insertbackground='#00ff00',
                                    relief=tk.FLAT, bd=0, highlightthickness=0)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', lambda e: self.start_agent())
        self.input_entry.focus()

    def create_result_section(self, parent):
        self.result_frame = tk.Frame(parent, bg='black')
        self.result_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        self.hop_label = tk.Label(self.result_frame, text='',
                                  fg='#00ff00', bg='black',
                                  font=self.small_font, anchor='w')
        self.hop_label.pack(fill=tk.X)

        # Result display
        self.result_text = tk.Text(self.result_frame, bg='black', fg='#00ff00',
                                   font=self.small_font, relief=tk.FLAT,
                                   wrap=tk.WORD, height=4, bd=0,
                                   highlightthickness=0)
        self.result_text.pack(fill=tk.X)

    def draw_node(self, x, y, label, is_active=False):
        radius = 6
        color = '#00ff00' if is_active else '#004400'

        # Draw node circle
        node_id = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                          fill=color, outline='#00ff00', width=1)

        # Draw label below node
        display_label = label if len(label) <= 35 else label[:32] + '...'
        text_id = self.canvas.create_text(x, y + 15,
                                          text=display_label, fill='#00ff00',
                                          font=self.small_font, anchor=tk.N)

        return node_id, text_id

    def draw_connection(self, x1, y1, x2, y2):
        return self.canvas.create_line(x1, y1, x2, y2, fill='#003300', width=1)

    def calculate_tree_positions(self, num_nodes):
        """Calculate positions in a binary tree layout"""
        positions = {}
        canvas_width = max(self.canvas.winfo_width(), 650)

        # Root at top center
        positions[0] = (canvas_width // 2, 30)

        if num_nodes > 1:
            row_height = 50
            nodes_per_row = 2
            base_spacing = 180

            for i in range(1, num_nodes):
                # Calculate which row
                row = 1
                temp_count = 1
                while temp_count <= i:
                    if temp_count + nodes_per_row > i:
                        break
                    temp_count += nodes_per_row
                    row += 1

                # Position within row
                nodes_before_row = sum(min(nodes_per_row, max(0, num_nodes - 1 - j * nodes_per_row))
                                       for j in range(row - 1))
                position_in_row = i - nodes_before_row - 1
                nodes_in_this_row = min(nodes_per_row, num_nodes - nodes_before_row - 1)

                # Calculate x position
                total_width = base_spacing * (nodes_in_this_row - 1) if nodes_in_this_row > 1 else 0
                start_x = (canvas_width - total_width) // 2
                x = start_x + (position_in_row * base_spacing)
                y = 30 + (row * row_height)

                positions[i] = (x, y)

        return positions

    def add_node_animated(self, label, is_final=False):
        self.current_step += 1

        # Recalculate all positions
        self.node_positions = self.calculate_tree_positions(self.current_step)

        # Clear canvas
        self.canvas.delete('all')

        # Draw all connections
        for i in range(1, self.current_step):
            x1, y1 = self.node_positions[i - 1]
            x2, y2 = self.node_positions[i]
            self.draw_connection(x1, y1, x2, y2)

        # Draw all nodes
        for i in range(self.current_step):
            x, y = self.node_positions[i]
            node_label = self.nodes[i] if i < len(self.nodes) else label
            is_active = (i == self.current_step - 1) or is_final
            self.draw_node(x, y, node_label, is_active)

        self.nodes.append(label)

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Auto-scroll to bottom
        self.canvas.yview_moveto(1.0)

        self.root.update()

    def display_final_result(self, result_text, hop_count):
        # Highlight all nodes
        self.canvas.delete('all')

        # Redraw all connections
        for i in range(1, len(self.nodes)):
            x1, y1 = self.node_positions[i - 1]
            x2, y2 = self.node_positions[i]
            self.draw_connection(x1, y1, x2, y2)

        # Redraw all nodes as active
        for i in range(len(self.nodes)):
            x, y = self.node_positions[i]
            self.draw_node(x, y, self.nodes[i], is_active=True)

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Display hop count
        self.hop_label.config(text=f'Number of hops: {hop_count}')

        # Display formatted result
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', f'{result_text}')

    def start_agent(self):
        task = self.input_entry.get().strip()
        if not task:
            return

        # Disable input
        self.input_entry.config(state='disabled')

        # Reset
        self.canvas.delete('all')
        self.nodes = []
        self.current_step = 0
        self.result_text.delete('1.0', tk.END)
        self.hop_label.config(text='')

        # Run agent in thread
        thread = threading.Thread(target=self.run_agent_thread, args=(task,))
        thread.daemon = True
        thread.start()

    def run_agent_thread(self, task):
        asyncio.run(self.run_agent(task))

    async def run_agent(self, task):
        # Add initial node
        self.add_node_animated('Query: ' + (task[:25] + '...' if len(task) > 25 else task))
        await asyncio.sleep(0.3)

        # Create agent with enhanced task
        enhanced_task = f"{task}\n\nIMPORTANT: Provide your final answer in a maximum of 3 clear, concise sentences."

        llm = ChatGoogle(model="gemini-flash-latest")
        agent = Agent(task=enhanced_task, llm=llm, use_vision=False)

        try:
            # Run agent and get history
            history = await agent.run()

            # Get all URLs visited from the history
            visited_urls = history.urls()

            # Track URL visit counts to distinguish actions
            url_visit_count = {}
            action_labels = ['Visited', 'Reading', 'Analyzing', 'Fact Checking', 'Parsing', 'Finalizing']

            # Add a node for each URL visited
            if visited_urls:
                for url in visited_urls:
                    if url and url != 'about:blank' and not url.startswith('data:'):
                        try:
                            # Extract clean domain
                            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                            if len(domain) > 35:
                                domain = domain[:32] + '...'
                        except:
                            domain = url[:35] if len(url) > 35 else url

                        # Track how many times we've seen this URL
                        if domain not in url_visit_count:
                            url_visit_count[domain] = 0

                        # Get the appropriate action label based on visit count
                        visit_index = url_visit_count[domain]
                        if visit_index < len(action_labels):
                            action = action_labels[visit_index]
                        else:
                            # If more than 6 visits, keep using "Finalizing"
                            action = 'Finalizing'

                        url_visit_count[domain] += 1

                        self.add_node_animated(f'{action}: {domain}')
                        await asyncio.sleep(0.2)

            # Extract result
            final_text = history.final_result()
            if not final_text:
                final_text = str(history)

            # Add completion node
            self.add_node_animated('Complete', is_final=True)

            # Display result
            hop_count = len(self.nodes) - 1  # Exclude query node
            self.display_final_result(final_text, hop_count)

        except Exception as e:
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', f'ERROR: {str(e)}')
            self.hop_label.config(text='Task failed')

        # Re-enable input
        self.root.after(0, lambda: self.input_entry.config(state='normal'))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MacTerminalUI()
    app.run()
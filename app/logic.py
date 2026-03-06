import os
from PIL import Image
from fpdf import FPDF
from database import Database

class Manager:
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')

    def __init__(self):
        self.db = Database()
        self.current_images = []
        self.current_index = -1
        self.current_folder = None
        self._cache = {} # Simple path -> QPixmap cache could be added in UI layer

    def scan_folder(self, folder_path):
        self.db.add_folder(folder_path)
        
        # Fast Scan: collect paths first
        image_paths = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(self.IMAGE_EXTENSIONS):
                    image_paths.append(os.path.join(root, file))
        
        # Batch DB update
        self.db.add_images_batch(image_paths)
        return self.load_folder(folder_path)

    def load_folder(self, folder_path):
        self.current_folder = folder_path
        # Fast Retrieval: Use path prefix instead of walking again
        self.current_images = self.db.get_images_in_folder(folder_path)
        
        # State persistence: Restore last position
        folder_data = self.db.get_folder_by_path(folder_path)
        last_path = folder_data[1] if folder_data else None
        
        if last_path and last_path in self.current_images:
            self.current_index = self.current_images.index(last_path)
        elif self.current_images:
            self.current_index = 0
        else:
            self.current_index = -1
        return self.current_images

    def get_all_images(self):
        self.current_folder = None
        self.current_images = self.db.get_all_images()
        self.current_index = 0 if self.current_images else -1
        return self.current_images

    def get_folders(self):
        return self.db.get_all_folders()

    def jump_to(self, index):
        if 0 <= index < len(self.current_images):
            self.current_index = index
            self.update_position()
            return self.get_current_image()
        return None

    def reset_all(self):
        self.db.clear_all()
        self.current_images = []
        self.current_index = -1
        self.current_folder = None

    def delete_current_image(self):
        if not (0 <= self.current_index < len(self.current_images)):
            return False
            
        path = self.current_images[self.current_index]
        try:
            # 1. Remove from DB
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM images WHERE path = ?", (path,))
                conn.commit()
            
            # 2. Remove from OS
            if os.path.exists(path):
                os.remove(path)
                
            # 3. Update internal list
            self.current_images.pop(self.current_index)
            
            # 4. Adjust index
            if not self.current_images:
                self.current_index = -1
            elif self.current_index >= len(self.current_images):
                self.current_index = len(self.current_images) - 1
            
            self.update_position()
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def update_position(self):
        if self.current_folder and 0 <= self.current_index < len(self.current_images):
            self.db.update_folder_state(self.current_folder, self.current_images[self.current_index])

    def archive_by_tag(self, tag_name, target_dir):
        import shutil
        images = self.db.get_images_by_tag(tag_name)
        if not images:
            return 0
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        count = 0
        for src in images:
            try:
                # Use copy2 to preserve metadata
                shutil.copy2(src, target_dir)
                count += 1
            except Exception:
                continue
        return count

    def get_current_image(self):
        if 0 <= self.current_index < len(self.current_images):
            path = self.current_images[self.current_index]
            data = self.db.get_image_data(path)
            tags = self.db.get_image_tags(data[0]) if data else []
            return {
                "path": path,
                "id": data[0] if data else None,
                "inspiration": data[1] if data else "",
                "tags": tags
            }
        return None

    def next_image(self):
        if self.current_images:
            self.current_index = (self.current_index + 1) % len(self.current_images)
        return self.get_current_image()

    def prev_image(self):
        if self.current_images:
            self.current_index = (self.current_index - 1) % len(self.current_images)
        return self.get_current_image()

    def save_inspiration(self, image_id, text):
        self.db.update_inspiration(image_id, text)

    def add_tag(self, image_id, tag_name):
        self.db.tag_image(image_id, tag_name)

    def remove_tag(self, image_id, tag_name):
        self.db.untag_image(image_id, tag_name)

    def get_all_tags(self):
        return self.db.get_all_tags()

    def filter_by_tag(self, tag_name):
        self.current_images = self.db.get_images_by_tag(tag_name)
        if self.current_images:
            self.current_index = 0
        else:
            self.current_index = -1
        return self.current_images

    def filter_untouched(self, folder_path=None):
        self.current_images = self.db.get_untouched_images(folder_path)
        if self.current_images:
            self.current_index = 0
        else:
            self.current_index = -1
        return self.current_images

    def export_to_pdf(self, output_path):
        import datetime
        images_with_info = self.db.get_images_with_inspiration()
        if not images_with_info:
            return False

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=10) # Smaller margin
            
            # Unicode Support - Professional Font Loading
            font_path = None
            bold_font_path = None
            if os.name == 'nt': # Windows
                win_fonts = "C:\\Windows\\Fonts\\"
                if os.path.exists(win_fonts + "msyh.ttc"):
                    font_path = win_fonts + "msyh.ttc"
                if os.path.exists(win_fonts + "msyhbd.ttc"):
                    bold_font_path = win_fonts + "msyhbd.ttc"
            
            if font_path:
                pdf.add_font("CustomMain", "", font_path)
                main_font = "CustomMain"
                if bold_font_path:
                    pdf.add_font("CustomMain", "B", bold_font_path)
                    has_bold = True
                else:
                    has_bold = False
            else:
                main_font = "Arial"
                has_bold = True # Arial has built-in bold
            
            for img_path, inspiration in images_with_info:
                if not os.path.exists(img_path):
                    continue
                    
                pdf.add_page()
                
                # 1. Header: Filename & Date (Compact)
                fname = os.path.basename(img_path)
                mtime = os.path.getmtime(img_path)
                fdate = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                
                pdf.set_font(main_font, size=9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, f"IMG: {fname} | DAT: {fdate}", ln=True, align='R')
                pdf.ln(2)
                
                # 2. Image (Large center)
                try:
                    with Image.open(img_path) as img:
                        w, h = img.size
                        aspect = w / h
                        display_w = 190
                        display_h = 190 / aspect
                        if display_h > 160: 
                            display_h = 160
                            display_w = 160 * aspect
                        
                        pdf.image(img_path, x=(210 - display_w) / 2, y=pdf.get_y(), w=display_w)
                        pdf.ln(display_h + 8)
                except Exception:
                    pdf.set_font(main_font, size=10)
                    pdf.cell(0, 10, "[Image Load Error]", ln=True)
                    pdf.ln(5)

                # 3. Inspiration: BOLD & LARGE (Gold Standard)
                pdf.set_text_color(0, 0, 0)
                if has_bold:
                    pdf.set_font(main_font, style='B', size=18)
                else:
                    pdf.set_font(main_font, size=20) # Larger fallback for emphasis
                
                pdf.multi_cell(0, 12, inspiration, align='C')
                
            pdf.output(output_path)
            return True
        except Exception as e:
            print(f"PDF Export failed: {e}")
            return False

    def export_inspiration_bundle(self, target_dir):
        """Copies inspired images to folder and creates a metadata.json report."""
        import json
        import shutil
        
        images_with_info = self.db.get_images_with_inspiration()
        if not images_with_info:
            return 0

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        report_data = []
        count = 0
        
        for img_path, inspiration in images_with_info:
            if not os.path.exists(img_path):
                continue
                
            fname = os.path.basename(img_path)
            dest_path = os.path.join(target_dir, fname)
            
            # If name exists, add prefix to avoid overwrite/loss
            if os.path.exists(dest_path):
                fname = f"{count}_{fname}"
                dest_path = os.path.join(target_dir, fname)

            try:
                shutil.copy2(img_path, dest_path)
                report_data.append({
                    "filename": fname,
                    "original_path": img_path,
                    "inspiration": inspiration
                })
                count += 1
            except Exception:
                continue

        # Write JSON Report
        json_path = os.path.join(target_dir, "metadata.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        return count

import os
import sys
import glob
import traceback
import tkinter as tk
import threading 
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont


class WatermarkApp:
    def __init__(self, master):
        self.master = master
        self.master.title("水印工具")
        self.root = master
        # 设置最小窗口大小
        self.master.minsize(800, 600)

        # 初始化变量
        self.watermark_type = tk.StringVar(value="default")
        self.text_content = tk.StringVar()
        self.font_size = tk.IntVar(value=60)
        self.text_color = tk.StringVar(value="white")
        self.position = tk.StringVar(value="右下")
        self.opacity = tk.DoubleVar(value=0.5)
        self.size_scale = tk.DoubleVar(value=1.0)
        self.watermark_image = None
        self.source_image = None 

        # 加载默认水印图片
        default_watermark_path = os.path.join(os.path.dirname(__file__), 'watermark.png')
        if os.path.exists(default_watermark_path):
            try:
                self.default_watermark = Image.open(default_watermark_path)
            except Exception as e:
                print(f"加载默认水印失败: {str(e)}")
                self.default_watermark = None
        else:
            self.default_watermark = None
        # 设置GUI
        self.setup_gui()

    def setup_gui(self):
        # 主布局
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="水印设置")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 水印类型选择
        ttk.Label(control_frame, text="水印类型:").pack(pady=5)
        ttk.Radiobutton(control_frame, text="默认水印", variable=self.watermark_type,
                        value="default", command=self.update_watermark).pack()
        ttk.Radiobutton(control_frame, text="文字水印", variable=self.watermark_type,
                        value="text", command=self.update_watermark).pack()
        custom_radio = ttk.Radiobutton(control_frame, text="自定义图片", variable=self.watermark_type,
                                       value="custom", command=self.load_custom_watermark)
        custom_radio.pack()

        # 文字水印设置
        self.text_frame = ttk.LabelFrame(control_frame, text="文字水印设置")
        ttk.Label(self.text_frame, text="请输入文字:").pack(fill=tk.X, pady=2)
        
        # 创建文字输入框和确认按钮的容器
        text_input_frame = ttk.Frame(self.text_frame)
        text_input_frame.pack(fill=tk.X, pady=2)
        
        # 文字输入框
        ttk.Entry(text_input_frame, textvariable=self.text_content).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 确认按钮
        ttk.Button(text_input_frame, text="确认", command=self.update_watermark).pack(side=tk.LEFT, padx=5)
     

        # 添加文字颜色选择
        ttk.Label(self.text_frame, text="文字颜色:").pack(fill=tk.X, pady=2)
        color_frame = ttk.Frame(self.text_frame)
        color_frame.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(color_frame, text="白色", variable=self.text_color,
                        value="white", command=self.update_watermark).pack(side=tk.LEFT)
        ttk.Radiobutton(color_frame, text="黑色", variable=self.text_color,
                        value="black", command=self.update_watermark).pack(side=tk.LEFT)

        # 初始隐藏文字水印设置
        self.text_frame.pack_forget()

        # 位置选择
        position_frame = ttk.LabelFrame(control_frame, text="位置设置")
        position_frame.pack(fill=tk.X, pady=5, padx=5)
        positions = ["左上", "右上", "左下", "右下", "居中"]
        position_combo = ttk.Combobox(position_frame, textvariable=self.position,
                                      values=positions, state="readonly")
        position_combo.pack(fill=tk.X, pady=5)
        position_combo.bind('<<ComboboxSelected>>', lambda _: self.update_watermark())

        # 透明度调整
        ttk.Label(control_frame, text="透明度:").pack(pady=5)
        ttk.Scale(control_frame, from_=0, to=1, variable=self.opacity,
                  orient=tk.HORIZONTAL, command=lambda _: self.update_watermark()).pack(fill=tk.X)

        # 大小调整
        ttk.Label(control_frame, text="大小:").pack(pady=5)
        ttk.Scale(control_frame, from_=0.1, to=2.0, variable=self.size_scale,
                  orient=tk.HORIZONTAL, command=lambda _: self.update_watermark()).pack(fill=tk.X)

        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="选择图片", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="批量处理", command=self.batch_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.save_image).pack(side=tk.LEFT, padx=5)

        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

    def update_preview(self, image):
        """更新预览图像"""
        if image:
            try:
                # 创建新的预览图像
                preview_image = image.copy()
                
                # 确保预览图片是RGB模式
                if preview_image.mode != 'RGB':
                    preview_image = preview_image.convert('RGB')

                # 获取预览区域大小
                preview_width = self.preview_label.winfo_width()
                preview_height = self.preview_label.winfo_height()
                
                # 如果预览区域还没有大小，使用默认值
                if preview_width <= 1 or preview_height <= 1:
                    preview_width = 600
                    preview_height = 400

                # 调整图片大小以适应预览区域
                ratio = min(preview_width/preview_image.size[0], 
                        preview_height/preview_image.size[1])
                new_size = (int(preview_image.size[0] * ratio), 
                        int(preview_image.size[1] * ratio))
                preview_image = preview_image.resize(new_size, Image.Resampling.LANCZOS)

                # 创建新的PhotoImage对象
                photo = ImageTk.PhotoImage(preview_image)
                
                # 更新标签
                self.preview_label.configure(image=photo)
                
                # 保持引用
                self.preview_label.image = photo
                self.current_preview = photo

            except Exception as e:
                print(f"更新预览失败: {str(e)}")
                traceback.print_exc()

    def update_watermark(self):
        """更新水印预览"""
        if self.source_image:
            try:
                # 创建原图副本
                result = self.source_image.copy()
                
                # 显示/隐藏文字水印设置框
                if self.watermark_type.get() == "text":
                    self.text_frame.pack(fill=tk.X, pady=5, after=self.text_frame.master.children['!radiobutton3'])
                    
                    # 处理文字水印
                    draw = ImageDraw.Draw(result)
                    text = self.text_content.get() or "水印文字"
                    
                    # 计算基础字体大小（基于图片尺寸）
                    base_size = min(result.size) // 20  # 调整基础大小
                    font_size = int(base_size * self.size_scale.get())
                    
                    try:
                        # 尝试加载支持中日文的字体
                        if sys.platform.startswith('win'):
                            font_paths = [
                                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                            ]
                        else:
                            font_paths = [
                                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                                "/System/Library/Fonts/PingFang.ttc",
                            ]
                        
                        font = None
                        for font_path in font_paths:
                            if os.path.exists(font_path):
                                font = ImageFont.truetype(font_path, font_size)
                                break
                                
                        if font is None:
                            font = ImageFont.load_default()
                            print("未找到支持中文的字体，使用默认字体")
                            
                    except Exception as e:
                        print(f"加载字体失败: {str(e)}")
                        font = ImageFont.load_default()
                    
                    # 创建临时图片用于文字绘制（支持透明度）
                    text_layer = Image.new('RGBA', result.size, (255, 255, 255, 0))
                    text_draw = ImageDraw.Draw(text_layer)
                    
                    # 获取文字边界框
                    text_bbox = text_draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # 计算文字位置
                    padding = 20
                    position = self.calculate_position(
                        (result.size[0] - padding * 2, result.size[1] - padding * 2),
                        (text_width, text_height)
                    )
                    position = (position[0] + padding, position[1] + padding)
                    
                    # 设置文字颜色和透明度
                    alpha = int(255 * self.opacity.get())
                    color = self.text_color.get()
                    fill_color = (255, 255, 255, alpha) if color == 'white' else (0, 0, 0, alpha)
                    
                    # 在临时图层上绘制文字
                    text_draw.text(position, text, font=font, fill=fill_color)
                    
                    # 将文字图层合并到结果图片上
                    result = Image.alpha_composite(result.convert('RGBA'), text_layer)
                    
                else:
                    self.text_frame.pack_forget()
                    watermark = self.get_watermark()
                    if watermark and not isinstance(watermark, dict):
                        # 处理图片水印
                        original_size = watermark.size
                        scale = self.size_scale.get()
                        new_size = (int(original_size[0] * scale),
                                  int(original_size[1] * scale))
                        watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
                        
                        # 调整透明度
                        watermark.putalpha(Image.eval(watermark.getchannel('A'),
                                                    lambda x: int(x * self.opacity.get())))
                        
                        # 计算位置并粘贴水印
                        position = self.calculate_position(result.size, watermark.size)
                        result.paste(watermark, position, watermark)

                # 更新预览
                self.update_preview(result)

            except Exception as e:
                print(f"更新水印失败: {str(e)}")
                traceback.print_exc()

    def get_watermark(self):
        """获取水印图像"""
        watermark_type = self.watermark_type.get()
        if watermark_type == "default":
            return self.create_default_watermark()
        elif watermark_type == "text":
            return self.create_text_watermark()
        elif watermark_type == "custom":
            return self.watermark_image
        return None

    def create_default_watermark(self):
        """创建默认水印"""
        try:
            if self.default_watermark:
                return self.default_watermark.copy()
            else:
               # 如果没有找到默认水印图片，使用之前的文字水印作为备选
                watermark = Image.new('RGBA', (200, 50), (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark)
                font = ImageFont.load_default()  # 添加这行
                text = "Default Watermark"
            
            # 获取文字大小
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
            
            # 计算文字位置使其居中
                x = (watermark.width - text_width) // 2
                y = (watermark.height - text_height) // 2
                draw.text((x, y), text, font=font, fill="white")
                return watermark
        except Exception as e:
            print(f"创建默认水印失败: {str(e)}")
            traceback.print_exc()
            return None

    def create_text_watermark(self):
        """创建文字水印"""
        try:
            # 只返回文字相关信息，不创建图片
            text = self.text_content.get() or "水印文字"
            color = self.text_color.get()
            return {
                'text': text,
                'color': color,
                'type': 'text'
            }
        except Exception as e:
            print(f"创建文字水印失败: {str(e)}")
            traceback.print_exc()
            return None

    def calculate_position(self, image_size, watermark_size):
        """计算水印位置"""
        position = self.position.get()
        padding = 10  # 边距

        if position == "左上":
            return (padding, padding)
        elif position == "右上":
            return (image_size[0] - watermark_size[0] - padding, padding)
        elif position == "左下":
            return (padding, image_size[1] - watermark_size[1] - padding)
        elif position == "右下":
            return (image_size[0] - watermark_size[0] - padding,
                   image_size[1] - watermark_size[1] - padding)
        else:  # 居中
            return ((image_size[0] - watermark_size[0]) // 2,
                   (image_size[1] - watermark_size[1]) // 2)

    def update_preview(self, image):
        """更新预览图像"""
        if image:
            try:
                # 设置预览的最大尺寸
                MAX_WIDTH = 800
                MAX_HEIGHT = 600
                
                # 获取原始尺寸
                width, height = image.size
                
                # 计算缩放比例
                scale_w = MAX_WIDTH / width
                scale_h = MAX_HEIGHT / height
                scale = min(scale_w, scale_h)  # 选择较小的缩放比例以适应窗口
                
                if scale < 1:  # 只有当图片太大时才缩小
                    # 计算新尺寸
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    
                    # 缩放图片
                    preview_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                elif max(width, height) < 400:  # 如果图片太小，放大到合适大小
                    scale = 400 / max(width, height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    preview_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    preview_image = image.copy()
                
                # 确保预览图片是RGB模式
                if preview_image.mode != 'RGB':
                    preview_image = preview_image.convert('RGB')

                # 更新预览
                if hasattr(self, 'current_preview'):
                    del self.current_preview
                self.current_preview = ImageTk.PhotoImage(preview_image)
                self.preview_label.configure(image=self.current_preview)
                self.preview_label.image = self.current_preview

            except Exception as e:
                print(f"更新预览失败: {str(e)}")
                traceback.print_exc()

    def load_image(self):
        """加载原始图片"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            try:
                # 加载并转换图片，移除色彩配置文件
                image = Image.open(file_path)
                image = image.convert('RGB')
                # 创建新图片以移除色彩配置文件
                new_image = Image.new('RGB', image.size)
                new_image.paste(image)
                self.source_image = new_image
                self.current_image_path = file_path
                self.update_watermark()
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {str(e)}")
                print(f"加载图片失败: {str(e)}")
                traceback.print_exc()

    def batch_process(self):
        """批量处理文件夹中的图片"""
        folder_path = filedialog.askdirectory(title="选择要处理的文件夹")
        if not folder_path:
            return

        try:
            # 获取所有支持的图片文件（修改文件搜索逻辑，避免重复）
            extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff')
            self.image_files = []
            for file in os.listdir(folder_path):
                if file.lower().endswith(extensions):
                    full_path = os.path.join(folder_path, file)
                    if os.path.isfile(full_path):  # 确保是文件而不是文件夹
                        self.image_files.append(full_path)

            if not self.image_files:
                messagebox.showwarning("警告", "所选文件夹中没有找到支持的图片文件")
                return

            # 排序文件列表，确保顺序一致
            self.image_files.sort()

            # 初始化批量处理状态
            self.current_index = 0
            self.is_batch_mode = True
            
            # 添加导航按钮到现有界面
            if not hasattr(self, 'nav_frame'):
                self.nav_frame = ttk.Frame(self.master)
                self.nav_frame.pack(fill=tk.X, pady=5, padx=10)
                
                # 添加信息标签
                self.info_label = ttk.Label(self.nav_frame, text="")
                self.info_label.pack(side=tk.LEFT, padx=5)
                
                # 添加导航按钮
                self.prev_btn = ttk.Button(self.nav_frame, text="上一张", command=self.prev_image)
                self.prev_btn.pack(side=tk.LEFT, padx=5)
                
                self.next_btn = ttk.Button(self.nav_frame, text="下一张", command=self.next_image)
                self.next_btn.pack(side=tk.LEFT, padx=5)
                
                self.process_btn = ttk.Button(self.nav_frame, text="开始处理", command=self.process_all_images)
                self.process_btn.pack(side=tk.RIGHT, padx=5)
                
                self.cancel_btn = ttk.Button(self.nav_frame, text="取消批量", command=self.cancel_batch)
                self.cancel_btn.pack(side=tk.RIGHT, padx=5)
            else:
                # 如果已经存在导航框架，更新它的显示
                self.nav_frame.pack(fill=tk.X, pady=5, padx=10)
            
            # 显示第一张图片
            self.show_current_image()
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败：{str(e)}")
            print(f"预览失败: {str(e)}")
            traceback.print_exc()

    def show_current_image(self):
        """显示当前索引的图片"""
        try:
            # 更新信息标签
            total_images = len(self.image_files)
            current_file = os.path.basename(self.image_files[self.current_index])
            self.info_label.config(text=f"图片 {self.current_index + 1}/{total_images}: {current_file}")
            
            # 加载并显示图片
            image = Image.open(self.image_files[self.current_index])
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 更新源图片
            self.source_image = image
            self.current_image_path = self.image_files[self.current_index]
            
            # 使用现有的更新水印方法
            self.update_watermark()
            
            # 更新导航按钮状态
            self.prev_btn['state'] = 'normal' if self.current_index > 0 else 'disabled'
            self.next_btn['state'] = 'normal' if self.current_index < total_images - 1 else 'disabled'
            
        except Exception as e:
            print(f"显示图片失败: {str(e)}")
            traceback.print_exc()

    def prev_image(self):
        """显示上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def next_image(self):
        """显示下一张图片"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_current_image()

    def cancel_batch(self):
        """取消批量处理模式"""
        self.is_batch_mode = False
        self.nav_frame.pack_forget()
        self.source_image = None
        self.current_image_path = None
        self.preview_label.configure(image='')

    def process_all_images(self):
        """开始批量处理所有图片"""
        if messagebox.askyesno("确认", "是否开始处理所有图片？"):
            try:
                folder_path = os.path.dirname(self.image_files[0])
                watermark_dir = os.path.join(folder_path, "watermark")
                if not os.path.exists(watermark_dir):
                    os.makedirs(watermark_dir)
                
                # 显示进度条
                progress_window = tk.Toplevel(self.master)
                progress_window.title("处理进度")
                progress_window.geometry("300x150")
                progress_window.transient(self.master)
                
                progress_label = ttk.Label(progress_window, text="正在处理...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, length=200, mode='determinate')
                progress_bar.pack(pady=10)
                
                total_files = len(self.image_files)
                processed_count = 0
                
                for i, image_path in enumerate(self.image_files, 1):
                    try:
                        # 更新进度
                        progress_bar['value'] = (i / total_files) * 100
                        progress_label['text'] = f"正在处理: {os.path.basename(image_path)}\n{i}/{total_files}"
                        progress_window.update()
                        
                        # 处理图片
                        image = Image.open(image_path)
                        if image.mode != 'RGBA':
                            image = image.convert('RGBA')
                        
                        # 创建带水印的图片副本
                        result = image.copy()
                        
                        # 获取水印设置
                        watermark = self.get_watermark()
                        if watermark:
                            if isinstance(watermark, dict) and watermark['type'] == 'text':
                                # 处理文字水印
                                text_layer = Image.new('RGBA', result.size, (255, 255, 255, 0))
                                text_draw = ImageDraw.Draw(text_layer)
                                
                                # 计算字体大小
                                base_size = min(result.size) // 20
                                font_size = int(base_size * self.size_scale.get())
                                
                                # 加载字体
                                try:
                                    if sys.platform.startswith('win'):
                                        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", font_size)
                                    else:
                                        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", font_size)
                                except:
                                    font = ImageFont.load_default()
                                
                                # 获取文字边界框
                                text = watermark['text']
                                text_bbox = text_draw.textbbox((0, 0), text, font=font)
                                text_width = text_bbox[2] - text_bbox[0]
                                text_height = text_bbox[3] - text_bbox[1]
                                
                                # 计算位置
                                padding = 20
                                position = self.calculate_position(
                                    (result.size[0] - padding * 2, result.size[1] - padding * 2),
                                    (text_width, text_height)
                                )
                                position = (position[0] + padding, position[1] + padding)
                                
                                # 设置文字颜色和透明度
                                alpha = int(255 * self.opacity.get())
                                color = watermark['color']
                                fill_color = (255, 255, 255, alpha) if color == 'white' else (0, 0, 0, alpha)
                                
                                # 绘制文字
                                text_draw.text(position, text, font=font, fill=fill_color)
                                result = Image.alpha_composite(result, text_layer)
                            else:
                                # 处理图片水印
                                original_size = watermark.size
                                scale = self.size_scale.get()
                                new_size = (int(original_size[0] * scale),
                                          int(original_size[1] * scale))
                                watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
                                watermark.putalpha(Image.eval(watermark.getchannel('A'),
                                                           lambda x: int(x * self.opacity.get())))
                                position = self.calculate_position(result.size, watermark.size)
                                result.paste(watermark, position, watermark)
                        
                        # 保存处理后的图片
                        filename = os.path.basename(image_path)
                        name, _ = os.path.splitext(filename)
                        save_path = os.path.join(watermark_dir, f"{name}_watermarked.jpg")
                        
                        if result.mode == 'RGBA':
                            result = result.convert('RGB')
                        result.save(save_path, quality=95)
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"处理图片失败 {image_path}: {str(e)}")
                        traceback.print_exc()
                
                progress_window.destroy()
                self.cancel_batch()  # 处理完成后退出批量模式
                
                if processed_count > 0:
                    messagebox.showinfo("完成", f"批量处理完成！\n成功处理 {processed_count} 个文件\n保存在 {watermark_dir} 文件夹中")
                else:
                    messagebox.showwarning("警告", "没有成功处理任何图片！")
                
            except Exception as e:
                messagebox.showerror("错误", f"批量处理失败：{str(e)}")
                print(f"批量处理失败: {str(e)}")
                traceback.print_exc()
                
    def load_custom_watermark(self):
        """加载自定义水印图片"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("PNG图片", "*.png"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            try:
                image = Image.open(file_path)
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                self.watermark_image = image
                self.watermark_type.set("custom")
                self.update_watermark()
            except Exception as e:
                messagebox.showerror("错误", f"加载水印图片失败: {str(e)}")
                print(f"加载水印图片失败: {str(e)}")
                traceback.print_exc()

    def save_image(self):
        """保存添加水印后的图片"""
        if not self.source_image:
            messagebox.showwarning("警告", "请先选择原图")
            return

        try:
            # 获取原图路径的目录
            original_dir = os.path.dirname(self.current_image_path)
            # 创建水印文件夹
            watermark_dir = os.path.join(original_dir, "watermark")
            if not os.path.exists(watermark_dir):
                os.makedirs(watermark_dir)
            
            # 生成新文件名
            original_filename = os.path.basename(self.current_image_path)
            filename_without_ext = os.path.splitext(original_filename)[0]
            new_filename = f"{filename_without_ext}_watermarked.jpg"
            file_path = os.path.join(watermark_dir, new_filename)
            
            # 创建带水印的图片副本
            result = self.source_image.copy()
            if result.mode != 'RGBA':
                result = result.convert('RGBA')

            watermark = self.get_watermark()
            if watermark:
                if isinstance(watermark, dict) and watermark['type'] == 'text':
                    # 处理文字水印
                    draw = ImageDraw.Draw(result)
                    text = watermark['text']
                    
                    # 计算基础字体大小
                    base_size = min(result.size) // 30
                    font_size = int(base_size * self.size_scale.get())
                    
                    try:
                        # 尝试加载支持中日文的字体
                        if sys.platform.startswith('win'):
                            font_paths = [
                                "C:/Windows/Fonts/msyh.ttc",
                                "C:/Windows/Fonts/simsun.ttc",
                                "C:/Windows/Fonts/msgothic.ttc",
                                "C:/Windows/Fonts/YuGothic.ttf"
                            ]
                        else:
                            font_paths = [
                                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                                "/System/Library/Fonts/PingFang.ttc",
                                "/System/Library/Fonts/Hiragino Sans GB.ttc"
                            ]
                        
                        font = None
                        for font_path in font_paths:
                            if os.path.exists(font_path):
                                font = ImageFont.truetype(font_path, font_size)
                                break
                                
                        if font is None:
                            font = ImageFont.load_default()
                            
                    except Exception as e:
                        print(f"加载字体失败: {str(e)}")
                        font = ImageFont.load_default()
                    
                    # 获取文字边界框
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # 确保文字完全显示在图片内
                    padding = 20
                    position = self.calculate_position(
                        (result.size[0] - padding * 2, result.size[1] - padding * 2),
                        (text_width, text_height)
                    )
                    position = (position[0] + padding, position[1] + padding)
                    
                    # 设置文字颜色和透明度
                    alpha = int(255 * self.opacity.get())
                    color = watermark['color']
                    fill_color = (255, 255, 255, alpha) if color == 'white' else (0, 0, 0, alpha)
                    
                    # 绘制文字
                    draw.text(position, text, font=font, fill=fill_color)
                else:
                    # 处理图片水印
                    original_size = watermark.size
                    new_size = (int(original_size[0] * self.size_scale.get()),
                              int(original_size[1] * self.size_scale.get()))
                    watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
                    watermark.putalpha(Image.eval(watermark.getchannel('A'),
                                               lambda x: int(x * self.opacity.get())))
                    position = self.calculate_position(result.size, watermark.size)
                    result.paste(watermark, position, watermark)

            # 保存图片
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            result.save(file_path, quality=100)
            messagebox.showinfo("成功", f"图片保存成功！保存在 {file_path}")

        except Exception as e:
            messagebox.showerror("错误", f"保存图片失败：{str(e)}")
            print(f"保存图片失败: {str(e)}")
            traceback.print_exc()

def main():
    root = tk.Tk()
    app = WatermarkApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
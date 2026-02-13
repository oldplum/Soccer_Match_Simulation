import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import random
import sys
from collections import deque

# ==========================================
# 第一部分：核心比赛逻辑
# ==========================================

class FoulException(Exception):
    def __init__(self, number_type):
        self.number_type = number_type

class FootballMatchSimulation:
    def __init__(self, home_name, away_name, home_data, away_data, 
                 gui_interface, 
                 has_extra_time=True, has_penalty=True):
        
        self.home_name = home_name
        self.away_name = away_name
        self.home_stats = home_data
        self.away_stats = away_data
        self.gui = gui_interface
        
        self.has_extra_time = has_extra_time
        self.has_penalty = has_penalty
        self.score = {home_name: 0, away_name: 0}
        self.match_stats = {home_name: {'good': 0, 'med': 0}, away_name: {'good': 0, 'med': 0}}
        
        self.last_number = None
        self.consecutive_count = 0
        self.in_sudden_event = False
        self.pending_rewards = [] 

    def print_log(self, text, color="black"):
        self.gui.append_text(text + "\n", color)

    def pause(self):
        self.gui.wait_for_button()

    def log_score(self):
        self.gui.update_scoreboard(
            self.score[self.home_name], 
            self.score[self.away_name]
        )
        self.print_log(f"    ★ 场上比分: {self.home_name} {self.score[self.home_name]} - {self.score[self.away_name]} {self.away_name}", color="blue")

    def format_time(self, current_minutes, start_minute, end_minute):
        base_m = int(current_minutes)
        seconds = int((current_minutes - base_m) * 60)
        if base_m >= end_minute:
            stoppage_m = base_m - end_minute
            return f"{end_minute}:00+{stoppage_m:02d}:{seconds:02d}"
        else:
            return f"{base_m:02d}:{seconds:02d}"

    def draw_number(self):
        num = random.choice([1, 2])
        if self.in_sudden_event: return num
        
        if num == self.last_number:
            self.consecutive_count += 1
        else:
            self.last_number = num
            self.consecutive_count = 1  
            
        if self.consecutive_count == 8:
            self.consecutive_count = 0 
            self.last_number = None
            raise FoulException(num)
        return num

    def calculate_chances(self, stats, opponent_gift):
        good, medium, _ = stats
        total_base = good + medium
        if total_base == 0: return 0, 0
        ratio_good = good / total_base
        ratio_med = medium / total_base
        final_good = good + opponent_gift * ratio_good
        final_med = medium + opponent_gift * ratio_med
        return max(1, int(round(final_good))), max(1, int(round(final_med)))

    def handle_save_rebound(self, attacking_team, defending_team):
        self.print_log(f"    - 【门将扑救】{defending_team} 门将做出关键扑救！球还在禁区！", color="purple")
        self.pause()
        res_clear = self.draw_number()
        if res_clear == 2:
            self.print_log(f"    - 【解围】{defending_team} 后卫大脚将球解围。进攻结束。")
            self.pause()
            return
        self.print_log(f"    - 球没踢远！混乱中...")
        self.pause()
        res_type = self.draw_number()
        if res_type == 2:
            self.print_log(f"    - 【角球】球出了底线，{attacking_team} 获得角球！")
            self.pause()
            self.play_good_chance(attacking_team, defending_team, custom_label="【角球机会】", count_override="(二次进攻)")
            return
        else:
            self.print_log(f"    - 【补射】{attacking_team} 球员跟进补射！")
            self.pause()
            shot_1 = self.draw_number()
            if shot_1 == 2: 
                self.print_log(f"    - 哎呀！补射打偏了！")
                self.pause()
                return
            shot_2 = self.draw_number()
            if shot_2 == 2:
                self.score[attacking_team] += 1
                self.print_log(f"    - ⚽ GOAL！！！补射空门得手！", color="green")
                self.log_score()
                self.pause()
            else:
                self.print_log(f"    - 神了！门将再次不可思议地扑出了补射！", color="purple")
                self.pause()
                self.handle_save_rebound(attacking_team, defending_team)

    def play_good_chance(self, attack, defend, time_str="", custom_label=None, count_override=None):
        is_home = (attack == self.home_name)
        target_pass = 1 if is_home else 2  
        target_shot = 1 if is_home else 2  
        target_goal = 2 if is_home else 1  
        target_save = 1 if is_home else 2  
        
        label = custom_label if custom_label else "【好机会】"
        if count_override: count_str = count_override
        elif custom_label: count_str = "" 
        else: count_str = f"(本场第 {self.match_stats[attack]['good']} 次)"

        display_time = f"[{time_str}] " if time_str else ""
        self.print_log(f"{display_time}{label} {attack} {count_str} 发起进攻...", color="darkblue")
        self.pause()
        
        n1 = self.draw_number()
        if n1 != target_pass:
            reason = "传球被截断" if is_home else "配合失误"
            self.print_log(f"    - {reason}。")
            self.pause()
            return
        self.print_log(f"    - 传球成功！直接起脚射门！")
        self.pause()
        n2 = self.draw_number()
        if n2 != target_shot:
            self.print_log(f"    - 射门打偏了。")
            self.pause()
            return
        self.print_log(f"    - 射正了！球向球门飞去...")
        self.pause()
        n3 = self.draw_number()
        if n3 == target_goal:
            self.score[attack] += 1
            self.print_log(f"    - ⚽ GOAL！！！！球进了！", color="green")
            self.log_score()
            self.pause()
        elif n3 == target_save:
            self.handle_save_rebound(attack, defend)

    def play_medium_chance(self, attack, defend, time_str=""):
        is_home = (attack == self.home_name)
        trigger_val = 1 if is_home else 2
        count_str = f"(本场第 {self.match_stats[attack]['med']} 次)"
        display_time = f"[{time_str}] " if time_str else ""
        
        self.print_log(f"{display_time}【中等机会】 {attack} {count_str} 尝试组织进攻...")
        self.pause()
        
        n1 = self.draw_number()
        if n1 == trigger_val:
            self.print_log(f"    - 漂亮的突破！中等机会转化为了好机会！", color="orange")
            self.pause()
            self.play_good_chance(attack, defend, custom_label="【机会升级】", count_override="(突破成功)")
        else:
            self.print_log(f"    - 进攻组织失败，球权转换。")
            self.pause()

    def resolve_foul(self, foul_type):
        self.in_sudden_event = True
        try:
            if foul_type == 1:
                fouling, victim = self.home_name, self.away_name
                self.print_log(f"\n⚡⚡⚡ 比赛中断！{fouling} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！", color="gold")
            else:
                fouling, victim = self.away_name, self.home_name
                self.print_log(f"\n⚡⚡⚡ 比赛中断！{fouling} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！", color="gold")
            self.pause()

            has_penalty, has_injury, has_red = False, False, False
            self.print_log(f"    - 裁判正在查看VAR...")
            self.pause()
            
            nature = self.draw_number()
            if nature == 1:
                self.print_log(f"    - 裁判指向点球点！", color="red")
                has_penalty = True
                if self.draw_number() == 1: has_injury = True
                if self.draw_number() == 1: has_red = True
            else:
                self.print_log(f"    - 恶劣犯规！球员受伤倒地！", color="red")
                has_injury = True
                if self.draw_number() == 1: has_penalty = True
                if self.draw_number() == 1: has_red = True
            self.pause()

            if has_red:
                self.print_log(f"    - 🟥 改判红牌！{fouling} 吃到红牌！{victim} 将获得额外好机会(延后)。", color="red")
                self.pause()
                self.pending_rewards.append((victim, 'good'))

            if has_injury:
                self.print_log(f"    - 🚑 担架进场，{victim} 球员受伤。{fouling} 获得战术优势(中等机会)！", color="orange")
                self.pause()
                self.pending_rewards.append((fouling, 'med'))

            if has_penalty:
                self.print_log(f"    - ！！罚点球时刻！！{victim} 主罚点球。", color="red")
                self.pause()
                self.shoot_penalty_kick(victim, fouling, is_shootout=False)

            self.print_log(f"    - 突发事件处理完毕，比赛恢复...\n")
            self.pause()
        finally:
            self.in_sudden_event = False

    def shoot_penalty_kick(self, kicker, keeper, is_shootout=False):
        is_home_kick = (kicker == self.home_name)
        self.print_log(f"    - {kicker} 球员站在点球点前...")
        self.pause()
        
        # 0.7 概率进球
        if random.random() < 0.7:
            goal = True
        else:
            goal = False
            
        if goal:
            self.print_log(f"    - ⚽ GOAL！骗过门将，点球罚进！", color="green")
            if not is_shootout:
                self.score[kicker] += 1
                self.log_score()
            self.pause()
            return True
        else:
            self.print_log(f"    - ❌ 点球被扑出来了！", color="purple")
            self.pause()
            if not is_shootout:
                self.handle_save_rebound(kicker, keeper)
            return False

    def check_penalty_winner(self, h_goals, a_goals, h_attempts, a_attempts):
        max_attempts = 5
        h_rem = max_attempts - h_attempts
        a_rem = max_attempts - a_attempts
        if h_goals > a_goals + a_rem: return self.home_name
        if a_goals > h_goals + h_rem: return self.away_name
        return None

    def run_penalty_shootout(self):
        self.in_sudden_event = True 
        self.print_log("\n=== 点球大战 ===", color="blue")
        self.pause()
        h_p, a_p = 0, 0
        h_att, a_att = 0, 0
        winner = None

        for i in range(1, 6):
            self.print_log(f"--- 第 {i} 轮 ---")
            h_att += 1
            if self.shoot_penalty_kick(self.home_name, self.away_name, is_shootout=True): h_p += 1
            self.print_log(f"    [点球比分] {self.home_name} {h_p} - {a_p} {self.away_name}", color="blue")
            winner = self.check_penalty_winner(h_p, a_p, h_att, a_att)
            if winner: break

            a_att += 1
            if self.shoot_penalty_kick(self.away_name, self.home_name, is_shootout=True): a_p += 1
            self.print_log(f"    [点球比分] {self.home_name} {h_p} - {a_p} {self.away_name}", color="blue")
            winner = self.check_penalty_winner(h_p, a_p, h_att, a_att)
            if winner: break
            
        if winner:
             self.print_log(f"\n★ 比赛结束！{winner} 赢得最终胜利！", color="red")
             self.pause()

        rounds = 5
        while h_p == a_p and not winner:
            rounds += 1
            self.print_log(f"--- 第 {rounds} 轮 (突然死亡) ---")
            if self.shoot_penalty_kick(self.home_name, self.away_name, is_shootout=True): h_p += 1
            if self.shoot_penalty_kick(self.away_name, self.home_name, is_shootout=True): a_p += 1
            self.print_log(f"    [点球比分] {self.home_name} {h_p} - {a_p} {self.away_name}", color="blue")
            if h_p != a_p:
                winner = self.home_name if h_p > a_p else self.away_name

        self.in_sudden_event = False 
        reg_h, reg_a = self.score[self.home_name], self.score[self.away_name]
        self.print_log("\n" + "="*40)
        self.print_log(f"全场比赛结束！")
        self.print_log(f"最终比分: {self.home_name} {reg_h} ({h_p}) : ({a_p}) {reg_a} {self.away_name}", color="red")
        self.print_log("="*40)
        self.gui.set_return_mode() 

    def play_half(self, half_name, home_chances, away_chances, start_minute, duration_minutes):
        self.print_log(f"\n=== {half_name} 开始 ===", color="blue")
        self.pause()
        
        initial_actions = []
        for _ in range(home_chances['good']): initial_actions.append((self.home_name, 'good'))
        for _ in range(home_chances['med']):  initial_actions.append((self.home_name, 'med'))
        for _ in range(away_chances['good']): initial_actions.append((self.away_name, 'good'))
        for _ in range(away_chances['med']):  initial_actions.append((self.away_name, 'med'))
        
        random.shuffle(initial_actions)
        action_queue = deque(initial_actions)
        
        initial_count = len(action_queue)
        avg_interval = duration_minutes / initial_count if initial_count > 0 else 5
        current_time = start_minute
        end_minute = start_minute + duration_minutes
        
        while action_queue:
            team, chance_type = action_queue.popleft() 
            current_time += avg_interval * random.uniform(0.6, 1.4)
            time_str = self.format_time(current_time, start_minute, end_minute)
            
            if chance_type == 'good': self.match_stats[team]['good'] += 1
            else: self.match_stats[team]['med'] += 1
            
            defender = self.away_name if team == self.home_name else self.home_name
            try:
                if chance_type == 'good': self.play_good_chance(team, defender, time_str=time_str)
                else: self.play_medium_chance(team, defender, time_str=time_str)
            except FoulException as e:
                self.resolve_foul(e.number_type)
                if self.pending_rewards:
                    self.print_log(f"    >>> 突发状况造成的额外机会已添加到本半场剩余时间中 ({len(self.pending_rewards)}个)。", color="orange")
                    self.pause()
                    for reward in self.pending_rewards: action_queue.append(reward)
                    self.pending_rewards = [] 

        self.print_log(f"=== {half_name} 结束，比分 {self.home_name} {self.score[self.home_name]} - {self.score[self.away_name]} {self.away_name} ===", color="blue")
        self.pause()

    def split_chances(self, total_good, total_med):
        h1_good = total_good // 2
        h2_good = total_good - h1_good
        h1_med = total_med // 2
        h2_med = total_med - h1_med
        return (h1_good, h1_med), (h2_good, h2_med)

    def run_match(self):
        h_good, h_med = self.calculate_chances(self.home_stats, self.away_stats[2])
        a_good, a_med = self.calculate_chances(self.away_stats, self.home_stats[2])
        
        self.print_log(f"比赛数据生成完毕：")
        self.print_log(f"{self.home_name} - 好机会:{h_good}, 中等机会:{h_med}")
        self.print_log(f"{self.away_name} - 好机会:{a_good}, 中等机会:{a_med}")
        self.print_log("\n比赛马上开始！点击[继续]吹哨", color="blue")
        self.pause()
        
        (h_g1, h_m1), (h_g2, h_m2) = self.split_chances(h_good, h_med)
        (a_g1, a_m1), (a_g2, a_m2) = self.split_chances(a_good, a_med)
        
        self.play_half("上半场", {'good': h_g1, 'med': h_m1}, {'good': a_g1, 'med': a_m1}, 0, 45)
        self.play_half("下半场", {'good': h_g2, 'med': h_m2}, {'good': a_g2, 'med': a_m2}, 45, 45)
        
        self.print_log(f"\n常规时间结束。比分: {self.score[self.home_name]} - {self.score[self.away_name]}", color="blue")
        self.pause()
        
        if self.score[self.home_name] == self.score[self.away_name]:
            if self.has_extra_time:
                self.print_log("\n平局！进入加时赛！", color="blue")
                self.pause()
                
                h_g_et = max(1, int(round(h_good / 4)))
                h_m_et = max(1, int(round(h_med / 4)))
                a_g_et = max(1, int(round(a_good / 4)))
                a_m_et = max(1, int(round(a_med / 4)))
                
                (h_g1, h_m1), (h_g2, h_m2) = self.split_chances(h_g_et, h_m_et)
                (a_g1, a_m1), (a_g2, a_m2) = self.split_chances(a_g_et, a_m_et)
                
                self.play_half("加时赛上半场", {'good': h_g1, 'med': h_m1}, {'good': a_g1, 'med': a_m1}, 90, 15)
                self.play_half("加时赛下半场", {'good': h_g2, 'med': h_m2}, {'good': a_g2, 'med': a_m2}, 105, 15)
                
                if self.score[self.home_name] == self.score[self.away_name]:
                    if self.has_penalty: 
                        self.run_penalty_shootout()
                    else: 
                        self.print_log("比赛平局结束！")
                        self.gui.set_return_mode() 
                else:
                    self.print_log("加时赛结束，决出胜负！", color="red")
                    self.gui.set_return_mode() 
            else:
                # 【修改】如果无加时赛，但有点球大战，则直接进点球
                if self.has_penalty:
                    self.print_log("\n常规时间平局，直接进入点球大战！", color="blue")
                    self.run_penalty_shootout()
                else:
                    self.print_log("比赛平局结束！")
                    self.gui.set_return_mode() 
        else:
             self.print_log("比赛结束！", color="red")
             self.gui.set_return_mode() 


# ==========================================
# 第二部分：GUI 界面封装类
# ==========================================

class FootballGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ 足球比赛模拟器 Pro")
        self.root.geometry("600x750")

        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True)

        self.frame_setup = None
        self.frame_match = None

        self.show_setup_ui()
        
        self.wait_event = threading.Event()
        self.label_score = None
        self.text_area = None
        self.btn_next = None

    def show_setup_ui(self):
        self.frame_setup = tk.Frame(self.main_container, pady=20)
        self.frame_setup.pack(fill="both", expand=True)

        tk.Label(self.frame_setup, text="赛前设置面板", font=("Arial", 20, "bold")).pack(pady=10)

        # 主队
        frame_h = tk.LabelFrame(self.frame_setup, text="主队设置", font=("Arial", 12), padx=10, pady=10)
        frame_h.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_h, text="球队名称:").grid(row=0, column=0, sticky="e")
        self.entry_h_name = tk.Entry(frame_h)
        self.entry_h_name.insert(0, "成都蓉城")
        self.entry_h_name.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(frame_h, text="好机会数:").grid(row=1, column=0, sticky="e")
        self.entry_h_good = tk.Entry(frame_h, width=5)
        self.entry_h_good.insert(0, "5")
        self.entry_h_good.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frame_h, text="中等机会:").grid(row=2, column=0, sticky="e")
        self.entry_h_med = tk.Entry(frame_h, width=5)
        self.entry_h_med.insert(0, "4")
        self.entry_h_med.grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(frame_h, text="送礼次数:").grid(row=3, column=0, sticky="e")
        self.entry_h_gift = tk.Entry(frame_h, width=5)
        self.entry_h_gift.insert(0, "3")
        self.entry_h_gift.grid(row=3, column=1, sticky="w", padx=5)

        # 客队
        frame_a = tk.LabelFrame(self.frame_setup, text="客队设置", font=("Arial", 12), padx=10, pady=10)
        frame_a.pack(fill="x", padx=20, pady=10)

        tk.Label(frame_a, text="球队名称:").grid(row=0, column=0, sticky="e")
        self.entry_a_name = tk.Entry(frame_a)
        self.entry_a_name.insert(0, "上海海港")
        self.entry_a_name.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(frame_a, text="好机会数:").grid(row=1, column=0, sticky="e")
        self.entry_a_good = tk.Entry(frame_a, width=5)
        self.entry_a_good.insert(0, "6")
        self.entry_a_good.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frame_a, text="中等机会:").grid(row=2, column=0, sticky="e")
        self.entry_a_med = tk.Entry(frame_a, width=5)
        self.entry_a_med.insert(0, "2")
        self.entry_a_med.grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(frame_a, text="送礼次数:").grid(row=3, column=0, sticky="e")
        self.entry_a_gift = tk.Entry(frame_a, width=5)
        self.entry_a_gift.insert(0, "5")
        self.entry_a_gift.grid(row=3, column=1, sticky="w", padx=5)
        
        frame_rules = tk.Frame(self.frame_setup)
        frame_rules.pack(pady=10)
        self.var_extra = tk.BooleanVar(value=True)
        self.var_penalty = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_rules, text="开启加时赛", variable=self.var_extra).pack(side="left", padx=10)
        tk.Checkbutton(frame_rules, text="开启点球大战", variable=self.var_penalty).pack(side="left", padx=10)

        tk.Button(self.frame_setup, text="开始比赛", font=("Arial", 16, "bold"), bg="#4CAF50", fg="white", 
                  command=self.start_game).pack(pady=20, ipadx=20)

    def show_match_ui(self, home, away):
        self.frame_setup.destroy() 
        self.frame_match = tk.Frame(self.main_container)
        self.frame_match.pack(fill="both", expand=True)

        frame_top = tk.Frame(self.frame_match, pady=20, bg="#f0f0f0")
        frame_top.pack(fill="x")
        
        tk.Label(frame_top, text=home, font=("Arial", 16, "bold"), bg="#f0f0f0", width=12).pack(side="left", padx=20)
        self.label_score = tk.Label(frame_top, text="0 - 0", font=("Impact", 40), bg="#f0f0f0", fg="#333")
        self.label_score.pack(side="left", expand=True)
        tk.Label(frame_top, text=away, font=("Arial", 16, "bold"), bg="#f0f0f0", width=12).pack(side="right", padx=20)

        self.text_area = scrolledtext.ScrolledText(self.frame_match, font=("Consolas", 11), state='disabled', padx=10, pady=10)
        self.text_area.pack(expand=True, fill="both", padx=10, pady=5)
        
        for color in ["red", "green", "blue", "purple", "orange", "darkblue"]:
            self.text_area.tag_config(color, foreground=color if color != "orange" else "#FFA500")
        self.text_area.tag_config("gold", foreground="#B8860B")

        self.btn_next = tk.Button(self.frame_match, text="继续 (Next)", font=("Arial", 14), 
                                  command=self.on_click_next, height=2, bg="#4CAF50", fg="white")
        self.btn_next.pack(fill="x", padx=10, pady=10)

    def start_game(self):
        try:
            h_name = self.entry_h_name.get()
            h_stats = [int(self.entry_h_good.get()), int(self.entry_h_med.get()), int(self.entry_h_gift.get())]
            
            a_name = self.entry_a_name.get()
            a_stats = [int(self.entry_a_good.get()), int(self.entry_a_med.get()), int(self.entry_a_gift.get())]
        except ValueError:
            messagebox.showerror("输入错误", "机会数据必须是整数！")
            return

        if not h_name or not a_name:
            messagebox.showerror("输入错误", "请输入球队名称！")
            return

        self.show_match_ui(h_name, a_name)

        rules = (self.var_extra.get(), self.var_penalty.get())
        t = threading.Thread(target=start_game_thread, args=(self, h_name, a_name, h_stats, a_stats, rules), daemon=True)
        t.start()

    def update_scoreboard(self, s1, s2):
        self.root.after(0, lambda: self.label_score.config(text=f"{s1} - {s2}"))

    def append_text(self, text, color="black"):
        def _update():
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, text, color)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        self.root.after(0, _update)

    def wait_for_button(self):
        self.root.after(0, lambda: self.btn_next.config(state='normal', text="继续 (Next)", bg="#4CAF50"))
        self.wait_event.wait()
        self.wait_event.clear()

    def on_click_next(self):
        self.btn_next.config(state='disabled', text="计算中...", bg="#9E9E9E")
        self.wait_event.set()

    def return_to_setup(self):
        """【新增】销毁比赛界面，回到设置界面"""
        self.frame_match.destroy()
        self.show_setup_ui()

    def set_return_mode(self):
        """【新增】将按钮改为返回模式"""
        self.root.after(0, lambda: self.btn_next.config(
            state='normal', 
            text="返回设置 (Return)", 
            bg="#2196F3", # 蓝色按钮
            command=self.return_to_setup
        ))


# ==========================================
# 线程入口函数
# ==========================================

def start_game_thread(gui, h_name, a_name, h_stats, a_stats, rules):
    game = FootballMatchSimulation(
        h_name, a_name, 
        h_stats, a_stats, 
        gui_interface=gui, 
        has_extra_time=rules[0], 
        has_penalty=rules[1]
    )
    game.run_match()

if __name__ == "__main__":
    root = tk.Tk()
    app = FootballGUI(root)
    root.mainloop()
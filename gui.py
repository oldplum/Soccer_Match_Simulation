import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random
import sys
from collections import deque

# ==========================================
# 第一部分：核心比赛逻辑 (已更新至最新版逻辑)
# ==========================================

class FoulException(Exception):
    def __init__(self, number_type):
        self.number_type = number_type

class FootballMatchSimulation:
    def __init__(self, home_name, away_name, home_data, away_data, 
                 gui_interface, # 接收 GUI 接口
                 has_extra_time=True, has_penalty=True):
        
        self.home_name = home_name
        self.away_name = away_name
        self.home_stats = home_data
        self.away_stats = away_data
        self.gui = gui_interface # 用于和界面通信
        
        self.has_extra_time = has_extra_time
        self.has_penalty = has_penalty
        self.score = {home_name: 0, away_name: 0}
        self.match_stats = {home_name: {'good': 0, 'med': 0}, away_name: {'good': 0, 'med': 0}}
        
        self.last_number = None
        self.consecutive_count = 0
        
        # 突发事件保护机制
        self.in_sudden_event = False
        self.pending_rewards = [] 

    # --- 适配 GUI 的输出与暂停 ---
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
        # 突发事件中不计数
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
                self.print_log(f"\n⚡⚡⚡ 比赛中断！检测到连续8个单数！{fouling} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！", color="red")
            else:
                fouling, victim = self.away_name, self.home_name
                self.print_log(f"\n⚡⚡⚡ 比赛中断！检测到连续8个双数！{fouling} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！", color="red")
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

            # 1. 红牌 (另一方获利)
            if has_red:
                self.print_log(f"    - 🟥 改判红牌！{fouling} 吃到红牌！{victim} 将获得额外好机会(延后)。", color="red")
                self.pause()
                self.pending_rewards.append((victim, 'good'))

            # 2. 受伤 (对方减员，犯规方获利)
            if has_injury:
                self.print_log(f"    - 🚑 担架进场，{victim} 球员受伤。{fouling} 获得战术优势(中等机会)！", color="orange")
                self.pause()
                self.pending_rewards.append((fouling, 'med'))

            # 3. 点球
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
        
        kick_res = self.draw_number()
        goal = (is_home_kick and kick_res == 1) or (not is_home_kick and kick_res == 2)
            
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
             self.print_log(f"\n★ 比赛提前结束！{winner} 胜局已定！", color="red")
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
        self.gui.disable_button()

    def play_half(self, half_name, home_chances, away_chances, start_minute, duration_minutes):
        self.print_log(f"\n=== {half_name} 开始 ===", color="blue")
        self.pause()
        
        initial_actions = []
        for _ in range(home_chances['good']): initial_actions.append((self.home_name, 'good'))
        for _ in range(home_chances['med']):  initial_actions.append((self.home_name, 'med'))
        for _ in range(away_chances['good']): initial_actions.append((self.away_name, 'good'))
        for _ in range(away_chances['med']):  initial_actions.append((self.away_name, 'med'))
        
        random.shuffle(initial_actions)
        # 使用 deque 实现队列
        action_queue = deque(initial_actions)
        
        initial_count = len(action_queue)
        avg_interval = duration_minutes / initial_count if initial_count > 0 else 5
        current_time = start_minute
        end_minute = start_minute + duration_minutes
        
        # 核心循环
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
                # 捕获突发事件
                self.resolve_foul(e.number_type)
                # 检查是否有待处理的奖励机会，加入队列末尾
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
                    if self.has_penalty: self.run_penalty_shootout()
                    else: self.print_log("比赛平局结束！")
            else:
                self.print_log("比赛平局结束！")
        else:
             self.print_log("比赛结束！", color="red")
             self.gui.disable_button()


# ==========================================
# 第二部分：GUI 界面封装类
# ==========================================

class FootballGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ 足球比赛模拟器 Pro")
        self.root.geometry("600x700")

        # 1. 顶部比分板
        self.frame_top = tk.Frame(root, pady=20, bg="#f0f0f0")
        self.frame_top.pack(fill=tk.X)
        
        self.label_home = tk.Label(self.frame_top, text="主队", font=("Arial", 16, "bold"), bg="#f0f0f0", width=10)
        self.label_home.pack(side=tk.LEFT, padx=20)
        
        self.label_score = tk.Label(self.frame_top, text="0 - 0", font=("Impact", 40), bg="#f0f0f0", fg="#333")
        self.label_score.pack(side=tk.LEFT, expand=True)
        
        self.label_away = tk.Label(self.frame_top, text="客队", font=("Arial", 16, "bold"), bg="#f0f0f0", width=10)
        self.label_away.pack(side=tk.RIGHT, padx=20)

        # 2. 中间日志框
        self.text_area = scrolledtext.ScrolledText(root, font=("Consolas", 11), state='disabled', padx=10, pady=10)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # 颜色标签
        self.text_area.tag_config("red", foreground="red")
        self.text_area.tag_config("green", foreground="green")
        self.text_area.tag_config("blue", foreground="blue")
        self.text_area.tag_config("purple", foreground="purple")
        self.text_area.tag_config("orange", foreground="#FFA500")
        self.text_area.tag_config("darkblue", foreground="darkblue")

        # 3. 底部按钮
        self.btn_next = tk.Button(root, text="继续 (Next)", font=("Arial", 14), command=self.on_click_next, height=2, bg="#4CAF50", fg="white")
        self.btn_next.pack(fill=tk.X, padx=10, pady=10)

        # 线程控制事件
        self.wait_event = threading.Event()
        
    def set_teams(self, home, away):
        self.label_home.config(text=home)
        self.label_away.config(text=away)

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

    def disable_button(self):
        self.root.after(0, lambda: self.btn_next.config(state='disabled', text="已结束", bg="#9E9E9E"))


# ==========================================
# 主程序入口
# ==========================================

def start_game_thread(gui):
    # 配置
    home_team = "成都蓉城"
    home_stats = [5, 4, 3] 
    
    away_team = "上海海港"
    away_stats = [6, 2, 5]  
    
    gui.set_teams(home_team, away_team)
    
    # 初始化游戏逻辑
    game = FootballMatchSimulation(
        home_team, away_team, 
        home_stats, away_stats, 
        gui_interface=gui, 
        has_extra_time=True, 
        has_penalty=True
    )
    
    game.run_match()

if __name__ == "__main__":
    root = tk.Tk()
    app = FootballGUI(root)
    
    t = threading.Thread(target=start_game_thread, args=(app,), daemon=True)
    t.start()
    
    root.mainloop()
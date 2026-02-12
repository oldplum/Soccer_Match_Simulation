import random
import sys
from collections import deque

class FoulException(Exception):
    """用于处理突发状况（8连号犯规）的中断信号"""
    def __init__(self, number_type):
        self.number_type = number_type  # 1 for odd (Home Foul), 2 for even (Away Foul)

class FootballMatchSimulation:
    def __init__(self, home_name, away_name, 
                 home_data, away_data,
                 has_extra_time=True,
                 has_penalty=True):
        
        self.home_name = home_name
        self.away_name = away_name
        self.home_stats = home_data
        self.away_stats = away_data
        
        self.has_extra_time = has_extra_time
        self.has_penalty = has_penalty
        
        self.score = {home_name: 0, away_name: 0}
        
        # 统计计数器
        self.match_stats = {
            home_name: {'good': 0, 'med': 0},
            away_name: {'good': 0, 'med': 0}
        }
        
        # 全局随机数监控
        self.last_number = None
        self.consecutive_count = 0
        
        # 突发事件状态锁
        self.in_sudden_event = False
        
        # 暂存突发事件中产生的奖励机会
        self.pending_rewards = [] 

    def pause(self):
        """暂停等待用户按回车"""
        try:
            input() 
        except Exception:
            pass

    def log_score(self):
        print(f"    ★ 场上比分: {self.home_name} {self.score[self.home_name]} - {self.score[self.away_name]} {self.away_name}")

    def format_time(self, current_minutes, start_minute, end_minute):
        base_m = int(current_minutes)
        seconds = int((current_minutes - base_m) * 60)
        if base_m >= end_minute:
            stoppage_m = base_m - end_minute
            return f"{end_minute}:00+{stoppage_m:02d}:{seconds:02d}"
        else:
            return f"{base_m:02d}:{seconds:02d}"

    def draw_number(self):
        """核心抽号方法"""
        num = random.choice([1, 2])
        
        # 如果在处理突发事件中，直接返回数字，不走计数逻辑
        if self.in_sudden_event:
            return num

        # 正常比赛流程，进行计数监控
        if num == self.last_number:
            self.consecutive_count += 1
        else:
            self.last_number = num
            self.consecutive_count = 1
            
        if self.consecutive_count == 8:
            self.consecutive_count = 0 
            self.last_number = None
            raise FoulException(num) # 抛出异常中断当前流程
            
        return num

    def calculate_chances(self, stats, opponent_gift):
        good, medium, _ = stats
        total_base = good + medium
        if total_base == 0:
            ratio_good, ratio_med = 0, 0
        else:
            ratio_good = good / total_base
            ratio_med = medium / total_base
        final_good = good + opponent_gift * ratio_good
        final_med = medium + opponent_gift * ratio_med
        return max(1, int(round(final_good))), max(1, int(round(final_med)))

    def handle_save_rebound(self, attacking_team, defending_team):
        print(f"    - 【门将扑救】{defending_team} 门将做出关键扑救！球还在禁区！(按回车...)", end="")
        self.pause()
        
        # 1. 判定解围
        res_clear = self.draw_number()
        if res_clear == 2:
            print(f"    - 【解围】{defending_team} 后卫大脚将球解围。进攻结束。")
            self.pause()
            return
        
        print(f"    - 球没踢远！混乱中...", end="")
        self.pause()
        res_type = self.draw_number()
        
        if res_type == 2:
            print(f"    - 【角球】球出了底线，{attacking_team} 获得角球！")
            self.pause()
            self.play_good_chance(attacking_team, defending_team, custom_label="【角球机会】", count_override="(二次进攻)")
            return
        else:
            print(f"    - 【补射】{attacking_team} 球员跟进补射！(按回车...)", end="")
            self.pause()
            
            shot_1 = self.draw_number()
            if shot_1 == 2: 
                print(f"    - 哎呀！补射打偏了！")
                self.pause()
                return
            
            shot_2 = self.draw_number()
            if shot_2 == 2:
                self.score[attacking_team] += 1
                print(f"    - ⚽ GOAL！！！补射空门得手！")
                self.log_score()
                self.pause()
            else:
                print(f"    - 神了！门将再次不可思议地扑出了补射！")
                self.pause()
                self.handle_save_rebound(attacking_team, defending_team)

    def play_good_chance(self, attack, defend, time_str="", custom_label=None, count_override=None):
        is_home = (attack == self.home_name)
        target_pass = 1 if is_home else 2  
        target_shot = 1 if is_home else 2  
        target_goal = 2 if is_home else 1  
        target_save = 1 if is_home else 2  
        
        label = custom_label if custom_label else "【好机会】"
        
        if count_override:
            count_str = count_override
        elif custom_label: 
            count_str = "" 
        else:
            count_str = f"(本场第 {self.match_stats[attack]['good']} 次)"

        display_time = f"[{time_str}] " if time_str else ""
        print(f"{display_time}{label} {attack} {count_str} 发起进攻...(按回车)", end="")
        self.pause()
        
        n1 = self.draw_number()
        if n1 != target_pass:
            reason = "传球被截断" if is_home else "配合失误"
            print(f"    - {reason}。")
            self.pause()
            return

        print(f"    - 传球成功！直接起脚射门！(按回车...)", end="")
        self.pause()
        
        n2 = self.draw_number()
        if n2 != target_shot:
            print(f"    - 射门打偏了。")
            self.pause()
            return

        print(f"    - 射正了！球向球门飞去...", end="")
        self.pause()
        
        n3 = self.draw_number()
        if n3 == target_goal:
            self.score[attack] += 1
            print(f"    - ⚽ GOAL！！！！球进了！世界波！")
            self.log_score()
            self.pause()
        elif n3 == target_save:
            self.handle_save_rebound(attack, defend)

    def play_medium_chance(self, attack, defend, time_str=""):
        is_home = (attack == self.home_name)
        trigger_val = 1 if is_home else 2
        
        count_str = f"(本场第 {self.match_stats[attack]['med']} 次)"
        display_time = f"[{time_str}] " if time_str else ""
        
        print(f"{display_time}【中等机会】 {attack} {count_str} 尝试组织进攻...(按回车)", end="")
        self.pause()
        
        n1 = self.draw_number()
        
        if n1 == trigger_val:
            print(f"    - 漂亮的突破！中等机会转化为了好机会！")
            self.pause()
            self.play_good_chance(attack, defend, custom_label="【机会升级】", count_override="(突破成功)")
        else:
            print(f"    - 进攻组织失败，球权转换。")
            self.pause()

    def resolve_foul(self, foul_type):
        """处理突发状况"""
        self.in_sudden_event = True
        
        try:
            if foul_type == 1:
                fouling_team = self.home_name
                victim_team = self.away_name
                print(f"\n⚡⚡⚡ 比赛中断！检测到连续8个单数！{fouling_team} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！")
            else:
                fouling_team = self.away_name
                victim_team = self.home_name
                print(f"\n⚡⚡⚡ 比赛中断！检测到连续8个双数！{fouling_team} 犯规！被裁判出示黄牌🟨 ！本次原进攻取消！")
            self.pause()

            has_penalty = False
            has_injury = False
            has_red = False

            print(f"    - 裁判正在查看VAR...(按回车)", end="")
            self.pause()
            
            # draw_number 不计数
            nature = self.draw_number()
            
            if nature == 1:
                print(f"    - 裁判指向点球点！(单数-必定点球)")
                has_penalty = True
                if self.draw_number() == 1: has_injury = True
                if self.draw_number() == 1: has_red = True
            else:
                print(f"    - 恶劣犯规！球员受伤倒地！(双数-必定受伤)")
                has_injury = True
                if self.draw_number() == 1: has_penalty = True
                if self.draw_number() == 1: has_red = True
            self.pause()

            # 1. 红牌处理
            # 逻辑：犯规方被罚下 -> 另一方多打少 -> 另一方获利
            if has_red:
                print(f"    - 🟥 裁判改判红牌！{fouling_team} 吃到红牌！{victim_team} 将获得一次额外好机会(延后执行)。")
                self.pause()
                self.pending_rewards.append((victim_team, 'good'))

            # 2. 受伤处理
            # 逻辑：被犯规方受伤 -> 实力削弱 -> 犯规方获利
            if has_injury:
                print(f"    - 🚑 担架进场，{victim_team} 核心球员受伤离场。由于对方减员，{fouling_team} 获得战术优势(中等机会)！")
                self.pause()
                # 【修正逻辑】犯规方获得机会
                self.pending_rewards.append((fouling_team, 'med'))

            # 3. 点球处理 (立即执行)
            # 点球肯定是给被犯规方的
            if has_penalty:
                print(f"    - ！！点球大战时刻！！{victim_team} 主罚点球。")
                self.pause()
                self.shoot_penalty_kick(victim_team, fouling_team, is_shootout=False)

            print(f"    - 突发事件处理完毕，比赛恢复...\n")
            self.pause()
            
        finally:
            self.in_sudden_event = False

    def shoot_penalty_kick(self, kicker, keeper, is_shootout=False):
        is_home_kick = (kicker == self.home_name)
        print(f"    - {kicker} 球员站在点球点前...(按回车)", end="")
        self.pause()
        
        kick_res = self.draw_number()
        
        goal = False
        if is_home_kick:
            if kick_res == 1: goal = True
        else:
            if kick_res == 2: goal = True
            
        if goal:
            print(f"    - ⚽ GOAL！骗过门将，点球罚进！")
            if not is_shootout:
                self.score[kicker] += 1
                self.log_score()
            self.pause()
            return True
        else:
            print(f"    - ❌ 点球被扑出来了！")
            self.pause()
            if not is_shootout:
                self.handle_save_rebound(kicker, keeper)
            return False

    def check_penalty_winner(self, h_goals, a_goals, h_attempts, a_attempts):
        max_attempts = 5
        h_remaining = max_attempts - h_attempts
        a_remaining = max_attempts - a_attempts
        if h_goals > a_goals + a_remaining: return self.home_name
        if a_goals > h_goals + h_remaining: return self.away_name
        return None

    def run_penalty_shootout(self):
        self.in_sudden_event = True 
        
        print("\n=== 点球大战 === (按回车)")
        self.pause()
        
        h_p_score = 0
        a_p_score = 0
        h_attempts = 0
        a_attempts = 0
        winner = None

        for i in range(1, 6):
            print(f"--- 第 {i} 轮 ---")
            
            h_attempts += 1
            if self.shoot_penalty_kick(self.home_name, self.away_name, is_shootout=True): h_p_score += 1
            print(f"    [点球比分] {self.home_name} {h_p_score} - {a_p_score} {self.away_name}")
            winner = self.check_penalty_winner(h_p_score, a_p_score, h_attempts, a_attempts)
            if winner: break

            a_attempts += 1
            if self.shoot_penalty_kick(self.away_name, self.home_name, is_shootout=True): a_p_score += 1
            print(f"    [点球比分] {self.home_name} {h_p_score} - {a_p_score} {self.away_name}")
            winner = self.check_penalty_winner(h_p_score, a_p_score, h_attempts, a_attempts)
            if winner: break
            
        if winner:
             print(f"\n★ 比赛提前结束！{winner} 胜局已定！")
             self.pause()

        rounds = 5
        while h_p_score == a_p_score and not winner:
            rounds += 1
            print(f"--- 第 {rounds} 轮 (突然死亡) ---")
            if self.shoot_penalty_kick(self.home_name, self.away_name, is_shootout=True): h_p_score += 1
            if self.shoot_penalty_kick(self.away_name, self.home_name, is_shootout=True): a_p_score += 1
            print(f"    [点球比分] {self.home_name} {h_p_score} - {a_p_score} {self.away_name}")
            if h_p_score != a_p_score:
                winner = self.home_name if h_p_score > a_p_score else self.away_name

        self.in_sudden_event = False 
        
        reg_h = self.score[self.home_name]
        reg_a = self.score[self.away_name]
        print("\n" + "="*40)
        print(f"全场比赛结束！")
        print(f"最终比分: {self.home_name} {reg_h} ({h_p_score}) : ({a_p_score}) {reg_a} {self.away_name}")
        print("="*40)

    def play_half(self, half_name, home_chances, away_chances, start_minute, duration_minutes):
        print(f"\n=== {half_name} 开始 (按回车) ===")
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
            
            time_step = avg_interval * random.uniform(0.6, 1.4)
            current_time += time_step
            time_str = self.format_time(current_time, start_minute, end_minute)
            
            if chance_type == 'good':
                self.match_stats[team]['good'] += 1
            else:
                self.match_stats[team]['med'] += 1
            
            defender = self.away_name if team == self.home_name else self.home_name
            
            try:
                if chance_type == 'good':
                    self.play_good_chance(team, defender, time_str=time_str)
                else:
                    self.play_medium_chance(team, defender, time_str=time_str)
            
            except FoulException as e:
                # 捕获突发事件
                self.resolve_foul(e.number_type)
                
                # 将突发事件产生的奖励机会加入队列末尾
                if self.pending_rewards:
                    print(f"    >>> 裁判示意：突发状况造成的额外机会已添加到本半场剩余时间中 ({len(self.pending_rewards)}个)。")
                    self.pause()
                    for reward in self.pending_rewards:
                        action_queue.append(reward)
                    self.pending_rewards = [] 

        print(f"=== {half_name} 结束，比分 {self.home_name} {self.score[self.home_name]} - {self.score[self.away_name]} {self.away_name} ===")
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
        
        print(f"比赛数据生成完毕：")
        print(f"{self.home_name} - 好机会:{h_good}, 中等机会:{h_med}")
        print(f"{self.away_name} - 好机会:{a_good}, 中等机会:{a_med}")
        print("\n请调整好坐姿，比赛马上开始！(按回车键吹哨)")
        self.pause()
        
        (h_g1, h_m1), (h_g2, h_m2) = self.split_chances(h_good, h_med)
        (a_g1, a_m1), (a_g2, a_m2) = self.split_chances(a_good, a_med)
        
        self.play_half("上半场", 
                       {'good': h_g1, 'med': h_m1}, 
                       {'good': a_g1, 'med': a_m1},
                       start_minute=0, duration_minutes=45)
        
        self.play_half("下半场", 
                       {'good': h_g2, 'med': h_m2}, 
                       {'good': a_g2, 'med': a_m2},
                       start_minute=45, duration_minutes=45)
        
        print(f"\n常规时间结束。比分: {self.score[self.home_name]} - {self.score[self.away_name]}")
        self.pause()
        
        if self.score[self.home_name] == self.score[self.away_name]:
            if self.has_extra_time:
                self.run_extra_time(h_good, h_med, a_good, a_med)
            else:
                print("根据规则，不进行加时赛。比赛平局结束！")
            
    def run_extra_time(self, h_g_base, h_m_base, a_g_base, a_m_base):
        print("\n平局！进入加时赛！(按回车)")
        self.pause()
        
        h_g_et = max(1, int(round(h_g_base / 4)))
        h_m_et = max(1, int(round(h_m_base / 4)))
        a_g_et = max(1, int(round(a_g_base / 4)))
        a_m_et = max(1, int(round(a_m_base / 4)))
        
        print(f"加时赛机会: {self.home_name}({h_g_et}/{h_m_et}) vs {self.away_name}({a_g_et}/{a_m_et})")
        self.pause()
        
        (h_g1, h_m1), (h_g2, h_m2) = self.split_chances(h_g_et, h_m_et)
        (a_g1, a_m1), (a_g2, a_m2) = self.split_chances(a_g_et, a_m_et)
        
        self.play_half("加时赛上半场", 
                       {'good': h_g1, 'med': h_m1}, 
                       {'good': a_g1, 'med': a_m1},
                       start_minute=90, duration_minutes=15)
        
        self.play_half("加时赛下半场", 
                       {'good': h_g2, 'med': h_m2}, 
                       {'good': a_g2, 'med': a_m2},
                       start_minute=105, duration_minutes=15)
        
        if self.score[self.home_name] == self.score[self.away_name]:
            if self.has_penalty:
                self.run_penalty_shootout()
            else:
                print("根据规则，不进行点球大战。比赛平局结束！")

# ================= 使用示例 =================

home_team = "成都蓉城"
home_stats = [5, 4, 3] 

away_team = "上海海港"
away_stats = [6, 2, 5]  

game = FootballMatchSimulation(
    home_team, 
    away_team, 
    home_stats, 
    away_stats,
    has_extra_time=True,  
    has_penalty=True      
)

game.run_match()
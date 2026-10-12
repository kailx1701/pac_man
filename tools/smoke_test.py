"""Chạy smoke test giao diện game cho mọi tổ hợp cấu hình được yêu cầu."""
import itertools
import traceback
import sys
from pathlib import Path

import turtle

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from maps.map import Map, TINY_SIZE, MEDIUM_SIZE, BIG_SIZE
from src.core.gameloop import GameSetup, GameState, launch_game, eat_pellets, fx_loop
from src.core.helper import cell_to_pixel, pixel_to_cell
from src.renderer.ui import clear_ui
from src.core.debug import log_exception


def run_ghost_visual_matrix(screen):
    """Chạy 20 giây mô phỏng cho từng số ma và chế độ sprite khả dụng."""
    import src.core.config as config
    import src.player.ghosts as ghost_module
    import src.renderer.sprites as sprite_defs

    results = []
    original_mode = ghost_module.GHOST_SPRITE_MODE
    modes = ["vector"]
    assets_exist = all((ghost_module._ASSET_DIR / filename).is_file()
                       for filename in ghost_module.GHOST_ASSETS.values())
    if assets_exist:
        modes.append("png")
    else:
        modes.append("png")  # Kiểm tra PNG ép dùng vẫn rơi về vector an toàn.

    for mode in modes:
        for count in range(1, 5):
            label = f"Ghost 20s vector/PNG-fallback count={count} mode={mode}"
            try:
                screen.clearscreen()
                sprite_defs._registered = False
                sprite_defs.register_all_shapes(screen)
                screen.tracer(0)
                ghost_module._known_shapes = None
                ghost_module._png_ready = None
                ghost_module.GHOST_SPRITE_MODE = mode
                config.GHOST_SPRITE_MODE = mode

                rows, cols = 26, 33
                walls = {(r, c) for r in range(rows) for c in range(cols)
                         if r in (0, rows - 1) or c in (0, cols - 1)}
                squad = ghost_module.GhostSquad(walls, rows, cols, count)
                spawns = [(4 + (i // 2) * 2, 5 + (i % 2) * 2) for i in range(count)]
                squad.set_start_positions(spawns)
                if any(ghost.move_speed != config.GHOST_SPEED for ghost in squad.ghosts):
                    raise AssertionError("Ghost speed did not follow GHOST_SPEED")
                pacman_cell = (13, 16)
                valid_shapes = set(screen.getshapes())
                shape_calls = {}
                for ghost in squad.ghosts:
                    calls = [0]
                    original_shape = ghost.shape

                    def counted_shape(name=None, base=original_shape, counter=calls):
                        if name is not None:
                            counter[0] += 1
                            return base(name)
                        return base()

                    ghost.shape = counted_shape
                    shape_calls[ghost] = calls

                calls_at_600 = {}
                for tick in range(1, 1201):
                    squad.update(pacman_cell, 0, tick=tick)
                    if tick == 600:
                        calls_at_600 = {ghost: counter[0] for ghost, counter in shape_calls.items()}
                    for ghost in squad.ghosts:
                        if not ghost.alive:
                            continue
                        if not ghost.isvisible():
                            raise AssertionError(f"{ghost.color_name} hidden on tick {tick}")
                        if abs(ghost.heading() - 90) > 0.01:
                            raise AssertionError(f"{ghost.color_name} heading={ghost.heading()}")
                        if ghost.get_grid_pos() in walls:
                            raise AssertionError(f"{ghost.color_name} entered a wall")
                        if ghost.shape() not in valid_shapes:
                            raise AssertionError(f"unregistered shape: {ghost.shape()}")
                details = ", ".join(
                    f"{ghost.color_name}={calls_at_600[ghost]}/600 shape() calls"
                    for ghost in squad.ghosts)
                if any(calls_at_600[ghost] >= 600 for ghost in squad.ghosts):
                    raise AssertionError(f"shape() not reduced: {details}")
                results.append((label, "PASS", details))

                if count == 1 and mode == "vector":
                    ghost = squad.ghosts[0]
                    gx, gy = ghost.xcor(), ghost.ycor()
                    ghost.kill()
                    if squad.check_collision_with_pacman(gx, gy):
                        raise AssertionError("dead ghost collided with Pacman")
                    ghost.respawn()
                    if not ghost.shape().startswith("ghost_scared"):
                        raise AssertionError(f"respawn shape is not scared: {ghost.shape()}")
                    if not ghost.isvisible() or squad.check_collision_with_pacman(gx, gy):
                        raise AssertionError("respawned invulnerable ghost was hidden or dangerous")
                    for tick in range(1, 61):
                        ghost.invuln_ticks -= 1
                        ghost.update_visual(tick)
                        if tick == 6 and not ghost.shape().startswith("ghost_scared_flash"):
                            raise AssertionError("invulnerability did not flash white at tick 6")
                        if tick == 12 and not ghost.shape().startswith("ghost_scared_"):
                            raise AssertionError("invulnerability did not return to blue at tick 12")
                        if not ghost.isvisible():
                            raise AssertionError("invulnerable ghost blinked out of view")
                    if ghost.invuln_ticks != 0 or not ghost.isvisible():
                        raise AssertionError("respawn invulnerability did not finish visibly")
                    if ghost.shape().startswith("ghost_scared"):
                        raise AssertionError("scared shape remained after invulnerability")
                    results.append(("Ghost kill/respawn/invulnerability", "PASS", ghost.shape()))
            except Exception as exc:
                log_exception(f"ghost visual matrix failed: {label}")
                results.append((label, "FAIL", str(exc)))
    ghost_module.GHOST_SPRITE_MODE = original_mode
    config.GHOST_SPRITE_MODE = original_mode
    return results


def run():
    setup = GameSetup()
    state = GameState(setup)
    screen = setup.screen
    results = []
    try:
        results.extend(run_ghost_visual_matrix(screen))
    except Exception as exc:
        log_exception("ghost visual matrix setup failed")
        results.append(("Ghost visual matrix setup", "FAIL", str(exc)))

    try:
        from src.core.search import Algorithm
        from src.core.problem import PacmanGameState, SingleFoodProblem

        grid = ["X" * 33] + ["X" + "." * 31 + "X" for _ in range(24)] + ["X" * 33]
        problem = SingleFoodProblem(grid, food_pos=(12, 20), start_pos=(12, 4))
        for name in ("a_star", "greedy", "bfs", "dfs", "ucs"):
            algorithm = Algorithm.from_name(name)
            result = algorithm.function(problem, 10000)
            if not result["is_solved"]:
                raise AssertionError(f"{name} failed: {result}")
        if Algorithm.from_name("a_star").function(problem, 10000)["path"] is None:
            raise AssertionError("Algorithm A* did not return a path")
        if Algorithm.from_name("none").function(problem) is not None:
            raise AssertionError("Algorithm none unexpectedly ran a search")

        minimax_grid = ["X" * 9] + ["X" + "." * 7 + "X" for _ in range(7)] + ["X" * 9]
        minimax_state = PacmanGameState((3, 3), [], [(3, 4)], minimax_grid)
        minimax_next = Algorithm.from_name("minimax").function(minimax_state, {(r, c) for r in range(9) for c in range(9) if minimax_grid[r][c] == "X"}, depth=2)
        if minimax_next is None:
            raise AssertionError("Minimax did not select a move")
        results.append(("Search Algorithm enum and 10s Auto core", "PASS", "5 search functions + Minimax invoked"))
    except Exception as exc:
        log_exception("search enum smoke case failed")
        results.append(("Search Algorithm enum and 10s Auto core", "FAIL", str(exc)))
    modes = (("BFS", True, "bfs"), ("A*", True, "a_star"),
             ("UCS", True, "ucs"), ("Greedy", True, "greedy"),
             ("DFS", True, "dfs"), ("Minimax", True, "minimax"))
    cases = list(itertools.product((1,), (False,), (("tiny", TINY_SIZE),), modes))
    cases.extend((count, random_map, ("tiny", TINY_SIZE), ("Manual", False, "NONE"))
                 for count in range(1, 5) for random_map in (False, True))
    try:
        for ghost_count, random_map, (size_name, size), (mode, auto, algorithm) in cases:
            label = f"ghosts={ghost_count} map={'Random' if random_map else 'Exist'} size={size_name} mode={mode}"
            try:
                state.running = False
                state.session += 1
                clear_ui(screen)
                screen.clearscreen()
                import src.renderer.sprites as sprite_defs
                sprite_defs._registered = False
                sprite_defs.register_all_shapes(screen)
                screen.tracer(0)

                setup.ghost_count = ghost_count
                setup.ghost = ghost_count > 0
                setup.map_size = size
                setup.auto_map_generate = random_map
                setup.auto_mode = auto
                setup.algorithm = algorithm
                setup.map = Map(auto_generate=random_map, size=size, ghost=setup.ghost)
                state.reset(setup)
                launch_game(setup, state)
                screen.update()

                expected_skill = not auto and ghost_count > 0
                if state.skill_enabled != expected_skill:
                    raise AssertionError(f"skill_enabled expected {expected_skill}, got {state.skill_enabled}")
                if auto and (state.skill_item is not None or state.skill_charges != 0):
                    raise AssertionError("Auto mode exposed skill state")

                actual = len(state.ghost_squad.ghosts) if state.ghost_squad else 0
                if actual != ghost_count:
                    raise AssertionError(f"ghost count expected {ghost_count}, got {actual}")
                if any(abs(ghost.heading() - 90) > 0.01 for ghost in state.ghost_squad.ghosts):
                    raise AssertionError("Ghost body orientation is not upright")
                if not callable(getattr(state, "_space_handler", None)):
                    raise AssertionError("Space handler was not registered")
                if auto and ghost_count:
                    original_ontimer = screen.ontimer
                    screen.ontimer = lambda _callback, _delay=0: None
                    state.has_started = True; state.is_paused = False; state.tick = 0
                    sid = state.session
                    for _ in range(20 * 60):
                        fx_loop(setup, state, sid)
                        if state.skill_item is not None or state.skill_charges != 0:
                            raise AssertionError("Auto mode created skill during 1200 ticks")
                        for ghost in state.ghost_squad.ghosts:
                            if ghost.alive and (not ghost.isvisible() or ghost.invuln_ticks != 0):
                                raise AssertionError("Auto ghost invariant failed during 1200 ticks")
                    screen.ontimer = original_ontimer
                    state.has_started = False; state.is_paused = True; state.tick = 0
                state._space_handler()

                def finish(current=state):
                    current.running = False
                    current.session += 1
                    screen._root.quit()

                screen.ontimer(finish, 10000 if auto else 3000)
                screen.mainloop()
                if not state.has_started:
                    raise AssertionError("Space countdown did not start the game")
                if auto:
                    if state.skill_item is not None or state.skill_charges != 0:
                        raise AssertionError("Auto mode acquired skill during run")
                    for ghost in state.ghost_squad.ghosts if state.ghost_squad else []:
                        if ghost.alive and (not ghost.isvisible() or ghost.invuln_ticks != 0):
                            raise AssertionError("Auto ghost visibility/invulnerability invariant failed")
                results.append((label, "PASS", ""))
            except Exception as exc:
                log_exception(f"smoke case failed: {label}")
                state.running = False
                state.session += 1
                details = traceback.format_exc()
                print(f"FAIL | {label}\n{details}")
                results.append((label, "FAIL", str(exc)))
                try:
                    screen._root.quit()
                except Exception:
                    log_exception("smoke screen quit failed")
        try:
            setup.auto_mode = False
            setup.algorithm = "NONE"
            setup.ghost_count = 2
            setup.ghost = True
            setup.map_size = TINY_SIZE
            setup.auto_map_generate = False
            setup.map = Map(auto_generate=False, size=TINY_SIZE, ghost=True)
            state.running = False
            state.session += 1
            clear_ui(screen)
            screen.clearscreen()
            import src.renderer.sprites as sprite_defs
            sprite_defs._registered = False
            sprite_defs.register_all_shapes(screen)
            screen.tracer(0)
            state.reset(setup)
            launch_game(setup, state)
            state.skill_enabled = True
            state.running = True; state.has_started = True; state.is_paused = False
            screen.ontimer = lambda _callback, _delay=0: None
            pellets = list(state.pellet_pen.stamps.items())[:10]
            if len(pellets) < 10:
                raise AssertionError("Manual test map has fewer than ten pellets")
            for (px, py), _stamp in pellets:
                state.pacman.goto(px, py)
                eat_pellets(state)
            if not state.pending_skill:
                raise AssertionError("Ten pellets did not request a skill item")
            sid = state.session
            fx_loop(setup, state, sid)
            item = state.skill_item
            if item is None or item.cell not in state.skill_valid_cells:
                raise AssertionError("Skill item did not spawn in reachable maze cells")
            state.pacman.goto(*cell_to_pixel(item.cell))
            fx_loop(setup, state, sid)
            if state.skill_charges != 1:
                raise AssertionError("Collecting SkillItem did not grant one charge")

            found = None
            for pac_cell in state.skill_valid_cells:
                for direction, (dr, dc) in (("up", (-1, 0)), ("down", (1, 0)),
                                             ("left", (0, -1)), ("right", (0, 1))):
                    ray = []; cell = pac_cell
                    while True:
                        nxt = (cell[0] + dr, cell[1] + dc)
                        if nxt not in state.skill_valid_cells or nxt in state.walls:
                            break
                        ray.append(nxt); cell = nxt
                    if ray:
                        found = (pac_cell, ray[-1], direction); break
                if found:
                    break
            if not found:
                raise AssertionError("No straight reachable corridor for skill shot")
            pac_cell, ghost_cell, direction = found
            from src.player.actors import Direction
            state.pacman.goto(*cell_to_pixel(pac_cell))
            state.pacman.direction = getattr(Direction, direction)
            ghost = state.ghost_squad.ghosts[0]
            ghost.set_grid_pos(*ghost_cell)
            state._space_handler()
            if ghost.alive or state.skill_charges != 0:
                raise AssertionError("Space did not spend a charge and kill the ghost in its ray")
            if ghost.respawn_ticks != 480:
                raise AssertionError("Killed ghost did not start a 480 tick respawn timer")
            for _ in range(480):
                fx_loop(setup, state, sid)
            if not ghost.alive or not ghost.isvisible() or ghost.invuln_ticks != 60:
                raise AssertionError("Ghost did not respawn visibly with 60 invulnerability ticks")
            for _ in range(60):
                fx_loop(setup, state, sid)
            if not ghost.alive or not ghost.isvisible() or ghost.invuln_ticks != 0:
                raise AssertionError("Respawned ghost did not return to visible normal state")
            results.append(("Manual skill pickup, shot, and respawn", "PASS", ""))
        except Exception as exc:
            log_exception("manual skill smoke case failed")
            results.append(("Manual skill pickup, shot, and respawn", "FAIL", str(exc)))
        try:
            original_ontimer = screen.ontimer
            screen.ontimer = lambda _callback, _delay=0: None
            for size_name, size in (("tiny", TINY_SIZE), ("medium", MEDIUM_SIZE), ("big", BIG_SIZE)):
                for random_map in (False, True):
                    state.running = False; state.session += 1
                    clear_ui(screen); screen.clearscreen()
                    import src.renderer.sprites as sprite_defs
                    sprite_defs._registered = False
                    sprite_defs.register_all_shapes(screen); screen.tracer(0)
                    setup.auto_mode = False; setup.algorithm = "NONE"
                    setup.ghost_count = 2; setup.ghost = True
                    setup.map_size = size; setup.auto_map_generate = random_map
                    setup.map = Map(auto_generate=random_map, size=size, ghost=True)
                    state.reset(setup); launch_game(setup, state)
                    state.has_started = True; state.is_paused = False
                    state.pending_skill = True
                    fx_loop(setup, state, state.session)
                    item = state.skill_item
                    label = f"SkillItem reachable cell {size_name} {'Random' if random_map else 'Exist'}"
                    if item is None or item.cell not in state.skill_valid_cells:
                        raise AssertionError(f"{label}: no item spawned inside reachable floor cells")
                    results.append((label, "PASS", ""))
                    item.hideturtle(); item.clear(); state.skill_item = None
            screen.ontimer = original_ontimer
            state.running = False; state.session += 1
        except Exception as exc:
            screen.ontimer = original_ontimer
            log_exception("skill map placement smoke case failed")
            results.append(("SkillItem map placement matrix", "FAIL", str(exc)))
        print("\nSMOKE TEST RESULTS")
        print("STATUS | CONFIGURATION | DETAILS")
        for label, status, details in results:
            print(f"{status:6} | {label} | {details}")
        passed = sum(status == "PASS" for _, status, _ in results)
        print(f"TOTAL: {passed}/{len(results)} PASS")
        return 0 if passed == len(results) else 1
    finally:
        try:
            state.running = False
            clear_ui(screen)
            screen.bye()
        except turtle.TurtleGraphicsError:
            log_exception("smoke screen cleanup failed")


if __name__ == "__main__":
    raise SystemExit(run())

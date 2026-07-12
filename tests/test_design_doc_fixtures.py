"""T-05: 设计文档案例自动校验（docs/design/ziwei/01-大限流年.md）。"""

from __future__ import annotations

from services.ziwei_engine.liuri import calc_liuri_branch, calc_liushi_branch


class TestDesignDocLiuriLiushi:
    """§五 流日/流时：流月初一顺行、流日子时顺行。"""

    def test_liuri_from_liuyue_wu_palace(self):
        # 流月在午宫(6)：初一=午，初二=未，初三=申
        assert calc_liuri_branch(6, 1) == 6
        assert calc_liuri_branch(6, 2) == 7
        assert calc_liuri_branch(6, 3) == 8

    def test_liushi_from_liuri_wu_palace(self):
        # 流日在午宫(6)：子时=午，丑时=未，寅时=申
        assert calc_liushi_branch(6, 0) == 6
        assert calc_liushi_branch(6, 1) == 7
        assert calc_liushi_branch(6, 2) == 8

    def test_liuri_liushi_chain(self):
        liuri_b = calc_liuri_branch(6, 3)  # 初三 → 申(8)
        assert calc_liushi_branch(liuri_b, 4) == (8 + 4) % 12  # 巳时

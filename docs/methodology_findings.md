# 방법론 점검 — 확정 결과 (축약본)

> 2026-06-21~24 방법론 점검(`an1.7`)의 결과물. 원래 두 문서(`methodology_review.md`, `methodology_revision_proposal.md`)였으나, 그 대부분이 **의도된 설계를 결함으로 오판**하고 학부 보고서 범위를 넘는 연구 재설계를 권고한 것으로 확인되어 **실제로 유효했던 2건만 남기고 축약**했다 (결정 D1-b, an1.10). 원문은 git 이력에 남아 있다 (`0049f15` 이전).
>
> 프로젝트 전체 기준 문서는 [STATUS.md](STATUS.md). 의도된 설계 목록(=고치면 안 되는 것)은 STATUS.md §1.

---

## 1. C2 — 테스트셋 임계값 누수 (진짜 버그, 수정 완료 `f685e81`)

**진단.** 최종 평가에서 호출되던 `evaluate_with_optimal_threshold(y_test, scores)`가 내부적으로 `find_optimal_threshold`를 써서 **테스트 레이블 `y_test`에 대해 G-Mean이 최대가 되는 임계값을 직접 탐색**했다. 8개 방법 전부 이 헬퍼를 공유했다.

**영향.** G-Mean / F1 / Precision / Recall / Specificity가 전부 낙관적으로 부풀려진다. AUC는 임계값과 무관하므로 영향 없음. 공통 헬퍼라 상대 순위는 부분적으로 보존되나, 점수 분포 모양에 따라 방법별 이득이 달라 순위도 왜곡될 수 있다.

**구조적 원인.** 최상위 분할이 train/test뿐이었고, 각 학습함수 내부의 검증셋은 **정상 데이터만**(`X_val_normal`) 담고 있었다. 사기 샘플이 없으면 G-Mean 최적 임계값을 고를 수 없으므로 → 테스트셋에서 고르게 된 것. 따라서 수정에는 **사기를 포함한 라벨드 홀드아웃**이 선행돼야 했다.

**수정 내용.**
- 데이터 셀에 `train_test_split(..., stratify=y_train)`으로 라벨드 홀드아웃 분할 추가 (`validation_split=0.2`), `X_holdout_scaled` / `X_holdout_pca` 생성.
- `evaluate_with_val_threshold(y_val_sel, val_scores, y_test, test_scores)` 신설 — 홀드아웃에서 임계값 선택, 테스트에서 보고.
- 8개 방법 전부 자기 모델·전처리로 홀드아웃을 채점한 뒤 새 평가자를 호출하도록 변경.

**대가 (수용됨, 결정 D2-a).** 946 → test 189 / holdout 151 / **train 757 → 606**. 기존 ppt 수치와 달라진다. 보고서 5장에 "임계값은 별도 홀드아웃에서 선택"을 명시하면 오히려 강점이 된다.

---

## 2. DIFE / LS-SWAP — 고유 측정기법 미구현 (수정 완료 `c655a92`)

### 2.1 무엇이 문제였나
두 방법 모두 이름이 가리키는 **distinctive 측정**이 코드에 없었다.
- `dife_qae_circuit`: 인코딩 + 변분층 후 그냥 `qml.expval(qml.PauliZ(0))`. compute-uncompute 없음, Projector 없음.
- `ls_swap_qae_circuit`: CNOT 3개로 만든 "local swap" 변분 패턴 후 `PauliZ(0)`. **SWAP 테스트가 아예 없음** (control·Hadamard·CSWAP 전무).

귀결: 둘은 엔탱글러 패턴만 다른 동일 계열 회로로 수렴해, "보조큐비트 없는 DIFE vs SWAP 기반"이라는 자원효율 비교 서사가 성립하지 않았다.

### 2.2 1차 출처 검증 (`docs/references/`)
사용자 제공 LLM 조사물이 인용한 출처를 직접 받아 대조했다.
- **Romero et al. 2017 (arXiv:1612.02806)** — 표준 QAE의 비용은 **trash 상태를 고정 reference |0⟩에 일치**시키도록 최대화한다 (Eq.7, SWAP 테스트는 *reference와 trash* 사이). ⇒ 표준 목적은 **trash 측정**이며, *latent*-vs-reference는 표준이 아니다.
- **Cerezo et al. 2021 (arXiv:2001.00550)** — **전역 비용함수 → 모든 깊이에서 barren plateau**(기울기 지수 감소), **국소 비용함수 → 최악 다항식 감소, O(log n) 깊이에서 훈련가능.** ⇒ DIFE(전역)/LS-SWAP(국소) 트레이드오프 서술은 옳고 인용 가능하다.

**원천 설계 PDF의 두 오류(독립 검증됨).**
1. DIFE를 `U†·U` 형태로 정의하면 **리셋 단계가 없어 U†U=I → 충실도≡1, 비용≡0, 기울기≡0**으로 퇴화한다. 어떤 입력·파라미터에서도 동일해 학습 불가.
2. LS-SWAP을 *latent*에 적용한 것은 Romero 기준 **역목적** — 정보를 담아야 할 잠재 큐비트를 고정 reference로 밀어붙여 잠재 정보를 파괴한다.

### 2.3 확정 정의 (구현됨)
| 방법 | 측정 = 비용 | 근거 | locality |
|---|---|---|---|
| enhanced-qVAE | 전체 trash ↔ \|0⟩ reference SWAP 테스트, C=1−F | Romero (표준) | 전역적 |
| **DIFE** | **ancilla-free 직접 trash 측정**, `qml.Projector([0]*n_trash, wires=trash)`, F=expval, C=1−F | Romero Eq.7 | trash만 → 덜 전역. 퇴화·전역비용 모두 회피 |
| **LS-SWAP** | **trash 부분집합**(n_swap < n_trash) ↔ reference SWAP, 단일 제어큐비트 `⟨Z_ctrl⟩`, F=(⟨Z⟩+1)/2 | Romero(목적) + Cerezo(국소→훈련가능) | 국소적 → barren plateau 완화 |

핵심: 국소-비용 훈련가능성 통찰을 **trash 부분집합 SWAP**으로 살리면 Romero의 올바른 목적과 Cerezo의 훈련가능성을 동시에 충족한다. DIFE는 직접 trash 측정으로 퇴화와 전역비용을 둘 다 피한다.

### 2.4 철회된 초기 서술
- ~~"QAE-Angle/DIFE/LS-SWAP은 오토인코더가 아니다"~~ → **오판.** 유니터리는 차원 보존·가역이라 고전 AE식 압축이 원천 불가하고, QAE의 압축은 trash를 |0⟩로 분리해 버리는 것으로만 성립한다 (Romero). 비용함수를 보면 **4종 모두 특정 trash 큐비트를 |0⟩로 모는 최소형 QAE**다. 올바른 판정 기준은 "표준 QAE 목적을 구현했는가"이며, 문제는 "비-QAE"가 아니라 "DIFE/LS-SWAP이 고유 측정을 빠뜨려 기본 QAE로 수렴"이었다.
- ~~"DIFE/LS-SWAP은 근거 없는 창작"~~ → **철회.** ancilla-free overlap 추정과 부분 SWAP은 실재하는 기법이다.
- ~~"QAE-Angle은 QAE가 아니다"~~ → **철회.** Huot(IEEE Access 2024)의 QAE-FD는 Rx 각도 인코딩 + 2 latent/2 trash + trash↔\|0⟩ fidelity 손실이며, 프로젝트 코드는 1 trash로 축소한 충실한 구현이다. **원조 baseline이므로 포함 필수.**

---

## 3. 검토했으나 적용하지 않은 것

아래는 점검 과정에서 "결함"으로 제기됐으나 **의도된 설계이거나 학부 보고서 범위를 넘어** 적용하지 않기로 한 항목이다. 다시 꺼내지 말 것 — 근거는 STATUS.md §1.

| 제기됐던 항목 | 처리 |
|---|---|
| 균형 50/50 데이터가 "고불균형" 설계와 배치 | **의도된 설계** (1:1 언더샘플링 946×30D) |
| 고전 30D vs 양자 PCA-4D 차원 교란 | **의도된 설계.** 단 지도교수 요청①에 따라 고전 PCA-4D 변형을 *추가* (`bde0fa7`) |
| RF를 자기재구성 이상탐지기로 쓰는 것이 비표준 | **의도된 설계** (ppt 규정). 유지 + 보고서에 caveat 한 줄 |
| QAE-Angle 구조 | **의도된 설계** = Huot QAE-FD |
| 주장을 "특성화 연구"로 재규정, 지도/비지도 tier 분리 | 범위 초과 — 보류 |
| 반복마다 재분할, 짝지은 유의성 검정, 다중비교 보정 | 범위 초과 — 보류 |
| barren plateau 큐비트 수 스윕 | 범위 초과 — 보류 (단 §2.2의 Cerezo 인용은 보고서에서 사용 가능) |
| 하이퍼파라미터 탐색 활성화, 잡음모델 강건성 | 범위 초과 — 보류 |

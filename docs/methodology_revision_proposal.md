# 방법론 적합성 검토 및 개정안 (Methodology Appropriateness & Revision Proposal)

> ⚠️ **정정(2026-06-24)**: 이 문서의 Part C/D는 본 연구를 엄밀 논문처럼 "재설계"하자고 제안하나, 실제 목표는 **학부 여름연구 보고서**이고 균형데이터·30D/4D·RF재구성은 *의도된 설계*다 → 대부분의 재설계 권고(주장 재규정·tier 분리·데이터 재설계·유의성검정·barren-plateau 스윕)는 **범위 초과로 보류**. 실제 사용된 유용한 핵심은 **D3-5(DIFE/LS-SWAP를 Romero/Cerezo 근거로 정정)** — 이것이 commit c655a92로 반영됨. 현재 단일 기준 문서: [STATUS.md](STATUS.md).

> 선행: [methodology_review.md](methodology_review.md) (Part A 코드 점검 · Part B 문서 자체 점검)
> 이 문서: **Part C** 방법론 적합성 판정 → **Part D** 개정안
> beads `an1.7` · 2026-06-21

---

# Part C — 방법론 자체의 적합성 판정

개정안을 쓰기 전에, 먼저 묻는다: **이 연구의 방법론이 그 목표에 애초에 적합한가?**

목표(epic/설계): "양자 vs 고전 사기탐지 기법의 공정·통계적 비교."

## C-0. 한 줄 판정
**현 방법론은 *틀리진 않았으나 주장 규모가 어긋나 있고(mis-scaled) 범주가 뒤섞여(category-confused) 있다.* 살릴 수 있지만, "양자 vs 고전 사기탐지" 같은 주장으로는 부적합하고, "소규모 통제 조건에서 양자 오토인코더 변형들의 특성화(characterization) 연구"로 재규정해야 적합해진다.**

## C-1. 연구질문이 답할 수 있게 설정됐는가 → 아니오(현재 규모로는)
4~8 큐비트 noiseless 시뮬레이터 + PCA 4D + n=946 toy 데이터로는 **"양자가 실제 FDS에서 우월한가"에 답할 수 없다.** NISQ 이점은 (i) 큐비트 수 확장, (ii) 실제 잡음, (iii) 현실적 데이터 규모·불균형에서만 의미를 갖는데 셋 다 없다. → 정직하고 적합한 질문은 좁다:
> "통제된 소규모 벤치마크에서, 이 양자 오토인코더 변형들이 고전 기준선 대비 탐지품질·훈련가능성·자원사용에서 어떻게 *특성화*되는가."
주장에서 "quantum advantage", "deployable FDS"를 빼고 *특성화/타당성 검증*으로 낮추면 방법론이 적합해진다.

## C-2. 선택한 방법들이 질문에 적합한가 → 부분적으로만
- 양자 오토인코더로 이상탐지: 정당한 연구방향. OK.
- 그러나 비지도 이상탐지(AE/QAE/IsolationForest)와 지도 분류기(RF)를 *한 비교축*에 놓은 건 **범주 오류**(Part B2a). 적합한 방법론은 *동류끼리* 비교한다: 이상탐지 vs 이상탐지를 본진으로, 지도 분류기는 "성능 상한/참조 tier"로 분리·명시.
- "구별된 4개 양자방법" 중 2개(DIFE·LS-SWAP)는 현재 깨졌거나 자명히 무의미(Part A C3 / Part B B1). 적합성을 위해선 *진짜로 구별되고 올바른* 4개로 고치거나, 올바른 것(QAE-Angle, enhanced-qVAE)만 두고 DIFE/LS-SWAP은 스펙 개정 후 편입.

## C-3. 데이터가 적합한가 → 아니오(현재), 조건부 가능
균형 50/50·946건은 FDS 주장엔 부적합(C1). *특성화* 연구로 낮춰도, 최소한 (a) "소규모 통제"임을 명시하고 (b) **현실적 불균형에서의 강건성**을 함께 보여야 적합. 권장: 현실적 불균형 데이터를 쓰되 resampling은 *학습 fold 내부에서만*, 평가는 현실적 동작점(operating point)에서.

## C-4. 평가가 적합한가 → 아니오(현재)
테스트셋 임계값(C2)·고정분할 CI(H3)·유의성검정 부재(M1)는 부적합. 검증셋 기반 임계값 + 반복/교차검증 분할 + 짝지은 검정이 필요. 지표(AUC/PR-AUC/G-Mean)는 *불균형 복원 시* 적합하나, 균형 데이터에선 PR-AUC와 불균형 서사가 무너진다.

## C-5. 자원·훈련가능성 분석이 적합한가 → 개념 보정 필요
큐비트/깊이/2큐비트게이트 수는 적절한 종속변인이나 *실제 회로에서 측정*해야 함(M3). barren plateau는 **큐비트 수 스윕**이 있어야 진단 가능(B2e) — 단일 크기 측정은 진단이 아니다. → barren plateau 주장을 빼거나, 작은 큐비트-수 스윕을 추가.

## C-6. 적합성 종합
방법론은 **다음 조건을 모두 충족할 때만 적합**하다: (1) 주장을 *특성화 연구*로 낮춤, (2) 패러다임 분리(이상탐지 본진 / 지도 참조), (3) 양자 4방법과 그 스펙을 올바르게 수정, (4) 남는 주장을 떠받치도록 데이터·평가 정비. Part D가 이 4가지를 개정안으로 구체화한다.

---

# Part D — 개정안

## D-1. 연구질문·주장 재정의 (선행)

| 현재(부적합) | 개정 |
|---|---|
| "양자 vs 고전 사기탐지 — 어느 게 우월한가" | "소규모 통제 벤치마크에서 양자 오토인코더 변형(QAE-Angle/enhanced-qVAE/DIFE/LS-SWAP)의 탐지품질·훈련가능성·자원사용 특성화, 고전 이상탐지·지도 기준선 대비" |
| quantum advantage / NISQ 배치 함의 | 명시적 한계: noiseless 시뮬, ≤8큐비트, PCA 4D, 소표본 — 일반화 주장 금지 |

## D-2. 실험설계 개정 (실험설계.txt 대체 항목)

**D2-1. 공정성의 1순위 통제는 *특징공간*, 그 위에서 tier 분리(H1 정정 반영).**
*정정 전제:* 현재 8개는 모두 정상학습 비지도 이상탐지다(RF도 자기재구성 AE). 따라서 핵심 통제는 패러다임이 아니라 **모든 방법이 같은 특징공간을 보게 하는 것**이다.
- **(필수) 특징공간 일치**: 양자가 PCA kD면 고전 이상탐지도 *동일 PCA kD*로 학습·평가 → "양자 vs 고전"을 차원 교란 없이 비교. (부가로 고전@전체차원을 "차원 제약 없는 참조"로 병기 가능.)
- **Tier A — 비지도 이상탐지(본진)**: Classical-AE, CNN-AE, IsolationForest, (선택)RF-AE, QAE-Angle, enhanced-qVAE, DIFE, LS-SWAP. 모두 정상학습·동일 특징공간·동일 프로토콜. 재구성형(AE/CNN/RF)과 분리형(IF)은 메커니즘이 달라도 *같은 task*라 공정 비교 가능.
- **Tier B — (선택) 지도 참조(성능 상한)**: 사용자가 원한 "넓은 비교"를 위해 *진짜* 지도 분류기(RandomForestClassifier/LogReg/XGBoost, 사기 레이블 사용)를 **별도 tier**로 추가. "레이블 있는 모델이 도달하는 상한" 맥락으로만 제시, Tier A와 동렬 순위표를 만들지 않음. (현 RF-as-AE의 비표준성은 별도 검토 — 표준 anomaly 기준선으로 둘지/지도 분류기로 되돌릴지 결정.)

**D2-2. 데이터·전처리(C1/C3).**
- 현실적 불균형 데이터로 평가(원본 Kaggle 불균형 유지 또는 검증된 불균형 표본). 균형 데이터를 쓰려면 *명시적으로 "통제 비교용"*으로만, 별도 ablation.
- 클래스 불균형 처리(undersampling/SMOTE 등)는 **학습 fold 내부에서만**, 검증/테스트엔 절대 적용 안 함(누수 방지).
- 특징공간 정책 명시(B2c): 양자=PCA kD(자원 제약), 고전=동일 PCA kD **및** 전체특징 두 버전 보고 → "양자가 진 게 차원 제약 때문인지" 분리. PCA는 train fold에서만 fit.

**D2-3. 분할·반복·통계(C2/H3/M1/B2d/B2f).**
- **3분할**: train / **labeled validation(사기 포함)** / test. 임계값·조기종료·(필요시)HP는 *validation에서만* 결정, **test는 단 한 번** 최종 측정.
- **반복 = 데이터 분할까지 재표집**: 반복마다 다른 시드로 stratified 재분할(또는 stratified k-fold ×반복). → mean±std/CI가 데이터 분산까지 포착(현재는 학습노이즈만).
- **유의성 검정**: 방법쌍 간 짝지은 검정(분할 공유 시 paired t / Wilcoxon signed-rank), 다중비교 보정(Holm/BH). "A>B"는 검정 통과 시에만 주장.
- **검정력**: 관심 효과크기(예: ΔAUC 0.02) 탐지에 필요한 반복·표본을 사전 추정. 작은 test면 반복수↑.

**D2-4. 공정 학습예산(B2b).**
- "에포크 100 고정" 대신 **수렴 기준(조기종료, validation loss patience)** 또는 **동일 계산예산(wall-clock/cost)** 으로 통제. 에포크 없는 RF엔 적용 불가함을 인정하고, 통제 대상은 *수렴 상태*로 재정의.
- 학습시간은 동일 하드웨어에서 측정(설계 유지).

**D2-5. 훈련가능성·자원·잡음(M2/M3/M5/B2e).**
- barren plateau: 큐비트 수 ∈ {4,6,8,…} **스윕**에서 cost 기울기 분산을 측정해 *크기에 따른 감소*를 보고(단일점 금지). 못 하면 해당 주장 삭제.
- 자원지표: 큐비트/회로깊이/2큐비트게이트 수를 **실제 컴파일된 회로에서** 자동 산출(`qml.specs`). 문서 수치와 회로 일치 검증.
- (선택) 잡음모델 하 성능저하 1세트라도 추가하면 NISQ 함의를 *제한적으로* 언급 가능.

## D-3. 양자 스펙 개정 (Technical specification.txt 대체)

### D3-0. 현 4종 확정 판정 (코드+비용함수+원논문 검증 / 2026-06-21 정정판)
**정정 경위**: 초판에서 "QAE-Angle/DIFE/LS-SWAP은 오토인코더가 아닌 단일-Pauli 스코어러"라 했으나 **오판이었다.** 비용함수를 보면 4종 모두 `fidelity=P(특정 trash 큐비트=\|0⟩)`를 1로 모는 = trash를 \|0⟩로 분리하는 **최소형 QAE**다(Romero/Huot 목적).

| 방법 | 코드 실제 동작 | 판정 |
|---|---|---|
| QAE-Angle | angle(Rx) 인코딩 → 마지막 큐비트 ⟨Z⟩→\|0⟩ 직접측정(1 trash), squared loss | ✅ **유효 최소 QAE = Huot QAE-FD(원논문)의 축소판. 포함 필수**(원조 baseline) |
| enhanced-qVAE | Araz 임베딩(병렬/재업로딩/교차) → 2-trash SWAP 테스트, linear loss | ✅ 유효 QAE(확장형). 큐비트 13할당/11사용 회계 정리 |
| DIFE | 임베딩+얽힘 → qubit0 ⟨Z₀⟩→\|0⟩ (F=⟨Z₀⟩ 미스케일) | ⚠️ 최소 QAE이나 **명세의 compute-uncompute 미구현** → 기본 QAE와 구별 안 됨 |
| LS-SWAP | 임베딩+CNOT"local swap" → qubit0 ⟨Z₀⟩→\|0⟩ | ⚠️ 최소 QAE이나 **SWAP 테스트 미구현** → 기본 QAE와 구별 안 됨 |

**원논문 검증(Huot 1612 IEEE Access)**: QAE-FD는 Rx 각도 인코딩 + 2latent/2trash + **trash↔\|0⟩ fidelity/Hamming 손실**(Romero[12]). 즉 QAE-Angle은 *원조 방법*이며 반드시 포함. (project 코드는 1 trash로 축소·measurement만 단순화한 충실 구현.)

→ **4종 모두 trash→\|0⟩ 최소 QAE다.** QAE-Angle·enhanced는 원논문/스펙에 충실(✅). 고칠 대상은 **DIFE·LS-SWAP의 *distinctive 측정기법*(코드가 빠뜨려 기본 QAE로 수렴)**. enhanced-qVAE/Huot/Romero를 템플릿으로 둘의 고유 기법을 구현.

#### 용어 정정 (문헌 대조)
"진짜 오토인코더"는 *틀린 기준*이다. 유니터리는 차원 보존·가역이라 고전 AE식 압축이 원천 불가하고, QAE의 압축은 trash를 \|0⟩로 분리해 *버리는 것*으로만 성립한다(명시적 디코더·재구성손실 없음; 학습신호는 trash 충실도). [Romero et al. 2017, arXiv:1612.02806] 게다가 본 연구는 *고전* 데이터를 각도 인코딩하므로 원 QAE(양자데이터 압축)에서 한 단계 더 떨어져 있다. 따라서 판정 기준은 "**표준 QAE 목적(잠재/trash 분리 + trash→reference 측정)을 구현했는가**"이며, 그 기준에서 enhanced-qVAE만 충족한다.

#### 원천 PDF(docs/...아키텍처...pdf) 설계 자체의 불건전성
DIFE/LS-SWAP은 *코드 버그를 넘어 설계 문서부터* 문제다:
- **DIFE (PDF §5.1)**: 회로를 `U_enc† S(x)† S(x) U_enc`로 정의 → S†S=I·U†U=I → **항등, 충실도≡1 (퇴화)**. 인용 기법[PDF ref 32]은 *서로 다른 두 상태*의 overlap 평가용인데, 같은 U 직후 U†는 자명히 1. 오적용.
- **LS-SWAP (PDF §5.2)**: "나머지 6 큐비트가 암묵적 trash"라면서 SWAP 테스트는 **잠재(0,1)** 를 reference와 비교 → trash가 아니라 잠재를 \|0⟩로 모는 *역(逆)목적*. 정당화도 hand-waving.
→ 결론: "원천 스펙대로 구현"은 유효한 목표가 아니며, D3 개정안(DIFE=직접 trash 측정, LS-SWAP=trash 부분 SWAP)이 *설계 자체의 정정*을 포함한다.

### D3-1~3. 개정 사양
전제: 4개를 *진짜로 구별되는 축* 위에 둔다 — **인코더는 전원 동일(enhanced 인코더)**, 구별축 = "trash 큐비트 충실도를 어떻게 추정하는가". 이래야 "측정 전략" 차이만 비교된다.

| 방법 | trash 충실도 추정 방식 | 보조큐비트 | 비고 |
|---|---|---|---|
| enhanced-qVAE | 전체 trash에 SWAP 테스트 (n_swap = n_trash) | n_trash + 1 | 기존 구조 *올바름*, 회계만 정리 |
| **LS-SWAP(개정)** | **축소** SWAP 테스트 (n_swap < n_trash) | < enhanced | D3-2. 자원↓ vs 추정정확도↓ trade-off가 곧 기여 |
| **DIFE(개정)** | ancilla-free, trash 직접 측정 (qml.probs) | 0 | D3-1. 가장 자원효율적 |
| **QAE-Angle(개정)** | 인코더만 angle-embedding으로 교체 + (enhanced와 동일) 전체 SWAP 테스트 | n_trash + 1 | D3-4. *임베딩* 효과를 분리하는 변형. 또는 'QAE 아님'으로 재명명해 별도 baseline |

공통 정의: n_data = n_latent + n_trash(trash는 data 큐비트의 *부분집합*, 별도 추가 레지스터 아님 — 현 enhanced의 N_TRASH 별도 큐비트 회계를 이 기준으로 재조정: total = n_data + n_swap + 1).

### D3-1. DIFE 개정 — degeneracy 제거
문제(B1a): compute 직후 같은 $U^\dagger$ → $U^\dagger U|0\rangle=|0\rangle$ 항등 → cost≡0.

**권장안(직접 trash 측정, ancilla-free, 비퇴화·표준):** uncompute를 쓰지 않고 trash 큐비트가 $|0\rangle$ 에 머무는 확률로 충실도 추정(Romero et al. 2017의 ancilla-free QAE).
```python
def dife_circuit(x, weights, n_data, n_latent):
    encoder_ansatz(x, weights)                 # U_enc on range(n_data)
    trash = list(range(n_latent, n_data))
    return qml.probs(wires=trash)              # P(trash=|0..0>) = probs[0]
# fidelity F = probs[0];  cost C = 1 - F   (비퇴화: trash 분리 학습해야만 F→1)
```
**대안(이름에 충실한 간섭형):** compute 후 trash를 **mid-circuit measure+reset**(비단위) 한 뒤 uncompute, $|0\dots0\rangle$ Projector 측정.
```python
def dife_circuit_interference(x, weights, n_data, n_latent):
    encoder_ansatz(x, weights)
    for q in range(n_latent, n_data):
        qml.measure(q, reset=True)             # 핵심: 비단위 단계
    qml.adjoint(encoder_ansatz)(x, weights)
    return qml.expval(qml.Projector([0]*n_data, wires=range(n_data)))
```
둘 다 cost C=1−F, ancilla 0. **권장: 직접 측정형**(가장 단순·증명적으로 비퇴화). (스펙 §3.5 `qml.Projector(*n_data,…)` 문법오류도 `[0]*n_data`로 정정.)

### D3-2. LS-SWAP 개정 — 측정 대상 정정(latent→trash) + 자원절감 정의
문제(B1b): latent를 reference와 SWAP → 잠재정보 파괴(목적 역전).

**개정:** SWAP 테스트를 **trash 큐비트**와 reference 사이에 수행(올바른 QAE 목적). "자원절감"은 *trash의 부분집합만* 또는 *축소된 reference 수*로 SWAP하여 큐비트를 줄이는 것으로 재정의(이게 enhanced 대비 진짜 차별점).
```python
def ls_swap_circuit(x, weights, n_data, n_latent, n_swap):   # n_swap ≤ n_trash
    encoder_ansatz(x, weights)                 # enhanced와 *동일* 인코더(데이터 재업로드/병렬임베딩 포함)
    ctrl = n_data + n_swap
    qml.Hadamard(ctrl)
    for i in range(n_swap):
        # trash_i (= n_latent+i)  vs  reference_i (= n_data+i)
        qml.CSWAP(wires=[ctrl, n_latent + i, n_data + i])
    qml.Hadamard(ctrl)
    return qml.expval(qml.PauliZ(ctrl))
# F = (expval+1)/2,  C = 1 - F.  Total qubits = n_data + n_swap + 1.
```
- enhanced-qVAE와의 **명확한 구별**: enhanced = 전체 trash SWAP(n_swap=n_trash, ref=n_trash). LS-SWAP = n_swap < n_trash(부분 추정 → 큐비트↓, 추정정확도↓의 trade-off). 이 trade-off가 LS-SWAP의 *연구 기여*가 된다.
- 인코더는 enhanced와 동일해야 함(현 코드의 단순 RY 인코딩은 폐기, B1 위반).
- 큐비트 회계: n_data=8, n_latent=6, n_trash=2, n_swap=2 → 8+2+1=11(스펙 수치와 일치하되 *대상은 trash*).

### D3-3. 손실/충실도 정의 일관화(M4)
- 모든 방법 cost = 1 − F(linear). enhanced/LS-SWAP: F=(⟨Z_ctrl⟩+1)/2. DIFE: F=P(trash=0). QAE-Angle: PauliZ proxy는 *진짜 fidelity가 아님*을 명시하거나 trash 측정형으로 교체 검토.
- "fidelity"라는 단어는 실제 충실도(SWAP/Projector/probs 기반)에만 사용. proxy는 proxy로 표기.

### D3-4. QAE-Angle 개정 (택1 결정 필요)
현 QAE-Angle은 QAE가 아니다(D3-0). 둘 중 하나로 정리:
- **(A 권장) 진짜 QAE로 승격**: 인코더를 angle-embedding(+데이터 재업로드)으로 두되, 측정을 enhanced와 *동일한 trash SWAP 테스트*로 교체. → 4종이 "**임베딩**(angle vs enhanced) × **측정**(full/reduced SWAP, ancilla-free)" 축에서 의미 있게 구별됨. 설계 의도("SWAP기반 QAE")와도 일치.
  ```python
  def qae_angle_circuit(x, weights, n_data, n_latent, n_swap):
      angle_encoder_ansatz(x, weights)            # angle embedding + re-upload
      return trash_swap_test(n_latent, n_data, n_swap)   # enhanced와 동일 측정
  ```
- **(B) QAE에서 제외·재명명**: "Variational One-Class Classifier (Angle)"로 이름 바꿔 *양자 baseline*으로만 유지(오토인코더 비교에서 빠짐). 현 단일-Pauli 구조 그대로, 단 'QAE/충실도' 표현 삭제.

### D3-5. 1차 출처 검증 결과 (Romero 1612.02806 · Cerezo 2001.00550) — 권위 있는 최종 정의
사용자의 LLM 조사물(`docs/DIFE 및 LS-SWAP...평가.pdf`)이 인용한 1차 출처를 직접 받아(→`docs/references/`) 대조했다.

**검증된 사실:**
- **Romero et al. 2017 (arXiv:1612.02806)** — 정전 QAE: 비용은 **trash 상태를 고정 reference \|0⟩에 일치**시키도록 최대화한다(Eq.7 "trash state fidelity"; SWAP 테스트는 *reference와 trash* 사이). reference는 고정 \|0⟩. ⇒ **표준 목적은 trash 측정**이며, *latent*-vs-reference는 표준이 아니다.
- **Cerezo et al. 2021 (arXiv:2001.00550)** — locality↔trainability: **전역(global) 비용함수 → 모든 깊이에서 barren plateau**(기울기 지수 감소); **국소(local) 비용함수 → 최악 다항식 감소, O(log n) 깊이에서 훈련가능.** ⇒ 평가보고서의 DIFE(전역)/LS-SWAP(국소) 트레이드오프는 **옳고 인용 가능**하다.

**평가보고서의 두 오류(독립 검증):** (1) DIFE "불완전 재구성→편차"는 *정확한 adjoint + 리셋 부재*에선 성립하지 않는다(U†U=항등 → 비용≡0). (2) LS-SWAP을 *latent*에 적용한 것은 Romero 기준 역목적. — 단, 국소/전역 통찰 자체는 타당.

**화해된 최종 정의(권고, 인용 포함):**
| 방법 | 측정 = 비용 | 근거 | locality |
|---|---|---|---|
| enhanced-qVAE | 전체 trash ↔ \|0⟩ reference SWAP 테스트, C=1−F | Romero(표준) | 전역적(주의) |
| **DIFE(확정)** | **ancilla-free 직접 trash 측정**, C=1−P(trash=\|0⟩) (`qml.probs`) | Romero Eq.7 | trash만 → 덜 전역. *compute-uncompute+전역 projector형은 리셋 없으면 퇴화 + 전역비용이라 비권장* |
| **LS-SWAP(확정)** | **trash 부분집합**(n_swap<n_trash) ↔ reference SWAP, 단일 제어큐비트 측정 | Romero(목적) + Cerezo(국소→훈련가능) | 국소적 → barren plateau 완화 |
| QAE-Angle | A/B (D3-4) | — | 측정 택1 따름 |

핵심: 평가보고서의 *국소-비용 훈련가능성* 통찰은 **trash 부분집합 SWAP**으로 살리면, *Romero의 올바른 목적*과 *Cerezo의 훈련가능성*을 동시에 충족한다(latent 오류 없이). DIFE는 직접 trash 측정으로 *퇴화·전역비용 둘 다* 회피한다.

## D-4. 개정 적용 순서(권고)
1. 본 개정안 합의 → 2. 스펙·설계 문서 개정 확정 → 3. 데이터(C1)·평가 프로토콜(C2/H3) 결정 → 4. 노트북/러너 코드 수정 + `qml.specs` 자원측정 + 유의성검정 추가 → 5. 소규모 검증런(스모크) → 6. `an1.3` 풀런 → 7. `an1.4` 보고 갱신.

> 본 문서는 *제안(개정안)*이다. 코드 변경 전, 특히 D1(주장 재규정)·D2-1(tier 분리)·D2-2(데이터)·D3(스펙)에 대한 사용자 승인이 필요하다.

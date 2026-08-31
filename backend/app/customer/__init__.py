"""Unit 2: Customer Ordering (고객 주문 · 박찬준).

고객용 백엔드 API — 자동 로그인, 메뉴 조회, 주문 생성, 현재 세션 주문 내역.
Unit 1 `core` 모듈(db/domain/models/errors/validation/pagination/security/sse)을
재사용하며 도메인 계산은 직접 하지 않고 core.domain 함수를 호출한다.

기준: shared/integration-contract.md §3.1,
      aidlc-docs/construction/unit2-customer/functional-design/*
"""

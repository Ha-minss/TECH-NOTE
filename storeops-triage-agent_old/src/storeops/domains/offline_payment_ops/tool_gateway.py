"""Offline payment read-only tool gateway adapter."""

from storeops.domains.offline_payment_ops.scenario_runtime import OfflinePaymentScenarioGateway

OfflinePaymentToolGateway = OfflinePaymentScenarioGateway

__all__ = ['OfflinePaymentScenarioGateway', 'OfflinePaymentToolGateway']

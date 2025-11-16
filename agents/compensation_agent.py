"""
Compensation Agent

Calculates and processes compensation claims for baggage issues.
Implements Montreal Convention compliance, receipt processing, and fraud detection.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import re
from .base_agent import BaseAgent


# Montreal Convention SDR limits (as of 2024)
# 1 SDR ≈ 1.37 USD (fluctuates)
SDR_TO_USD = 1.37
MONTREAL_CONVENTION_LIMIT_SDR = 1288  # SDRs per passenger
MONTREAL_CONVENTION_LIMIT_USD = int(MONTREAL_CONVENTION_LIMIT_SDR * SDR_TO_USD)  # ~$1,764


# Approval thresholds (USD)
APPROVAL_THRESHOLDS = {
    "auto_approve": 200,       # < $200: Auto-approve
    "supervisor": 500,         # $200-500: Supervisor approval
    "manager": float('inf')    # > $500: Manager approval
}


# Essential vs non-essential items categorization
ESSENTIAL_ITEMS = [
    "toiletries", "toothbrush", "toothpaste", "deodorant", "soap", "shampoo",
    "underwear", "socks", "basic clothing", "t-shirt", "pants", "shirt",
    "medications", "prescription", "medical supplies",
    "phone charger", "adapter", "basic necessities"
]

NON_ESSENTIAL_ITEMS = [
    "luxury", "designer", "electronics", "jewelry", "accessories",
    "entertainment", "souvenirs", "gifts", "perfume", "cosmetics"
]


# Copa Miles conversion rates (miles per USD)
COPA_MILES_PER_USD = 100


class CompensationAgent(BaseAgent):
    """
    Handles compensation calculations and claim processing.

    Capabilities:
    - Montreal Convention compliance
    - Receipt processing with OCR + LLM
    - Multi-tier approval workflow
    - Fraud detection
    - Goodwill gesture recommendations
    - Expense categorization (essential vs non-essential)
    - Currency conversion
    - Interim expense processing
    """

    def __init__(self, llm_client=None, db_connection=None, config=None):
        """Initialize CompensationAgent."""
        super().__init__(
            agent_name="compensation_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )

        # Fraud detection thresholds
        self.FRAUD_THRESHOLDS = {
            "max_claims_per_year": 3,
            "max_total_claimed_per_year": 5000,  # USD
            "duplicate_claim_similarity": 0.8,
            "suspicious_receipt_score": 0.7
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute compensation calculation and claim processing.

        Args:
            input_data: Dictionary containing:
                - claim_id: Claim identifier (optional, will generate if not provided)
                - incident_id: Incident ID from database
                - bag_tag: Bag tag number
                - passenger_id: Passenger identifier
                - incident_type: Type of incident (delayed/lost/damaged/pilferage)
                - delay_hours: Delay duration (if applicable)
                - declared_value: Customer's declared value
                - receipts: List of receipt data (optional)
                - interim_expenses: Boolean, whether interim expenses claimed
                - currency: Currency of claim (default: USD)

        Returns:
            Dictionary containing:
                - claim_number: Generated claim number
                - eligible: Whether compensation is eligible
                - compensation_amount: Calculated compensation
                - breakdown: Detailed calculation breakdown
                - approval_status: auto_approved/pending_supervisor/pending_manager
                - approver_required: Who needs to approve
                - required_documents: List of needed documents
                - fraud_risk_score: 0-1 fraud risk assessment
                - fraud_indicators: List of fraud red flags
                - goodwill_recommendations: Suggested goodwill gestures
                - processing_timeline: Expected processing time
        """
        self.validate_input(input_data, ["incident_id", "bag_tag", "passenger_id", "incident_type"])

        incident_id = input_data["incident_id"]
        bag_tag = input_data["bag_tag"]
        passenger_id = input_data["passenger_id"]
        incident_type = input_data["incident_type"]
        delay_hours = input_data.get("delay_hours", 0)
        declared_value = input_data.get("declared_value", 0)
        receipts = input_data.get("receipts", [])
        interim_expenses = input_data.get("interim_expenses", False)
        currency = input_data.get("currency", "USD")

        self.logger.info(
            f"Processing compensation claim for incident {incident_id}, "
            f"type: {incident_type}, bag: {bag_tag}"
        )

        # Step 1: Fetch incident and passenger data
        incident_data = await self._fetch_incident_data(incident_id, passenger_id, bag_tag)

        # Step 2: Generate claim number
        claim_number = await self._generate_claim_number(incident_id)

        # Step 3: Check fraud indicators
        fraud_assessment = await self._assess_fraud_risk(
            passenger_id=passenger_id,
            incident_type=incident_type,
            declared_value=declared_value,
            receipts=receipts,
            incident_data=incident_data
        )

        # Step 4: Check eligibility
        eligibility = await self._check_eligibility(
            incident_type=incident_type,
            incident_data=incident_data,
            fraud_assessment=fraud_assessment
        )

        if not eligibility["eligible"]:
            return {
                "claim_number": claim_number,
                "eligible": False,
                "ineligibility_reason": eligibility["reason"],
                "fraud_risk_score": fraud_assessment["risk_score"],
                "next_steps": eligibility.get("next_steps", [])
            }

        # Step 5: Process receipts if provided
        receipt_analysis = None
        if receipts and interim_expenses:
            receipt_analysis = await self._process_receipts(receipts, incident_type)

        # Step 6: Calculate compensation
        compensation_calc = await self._calculate_compensation(
            incident_type=incident_type,
            delay_hours=delay_hours,
            declared_value=declared_value,
            incident_data=incident_data,
            receipt_analysis=receipt_analysis,
            currency=currency
        )

        # Step 7: Determine approval workflow
        approval_decision = await self._determine_approval_workflow(
            compensation_amount=compensation_calc["total_amount"],
            fraud_risk_score=fraud_assessment["risk_score"],
            incident_type=incident_type,
            passenger_tier=incident_data.get("passenger", {}).get("loyalty_tier", "Standard")
        )

        # Step 8: Generate goodwill recommendations
        goodwill = await self._recommend_goodwill_gestures(
            incident_type=incident_type,
            incident_data=incident_data,
            compensation_amount=compensation_calc["total_amount"],
            fraud_risk_score=fraud_assessment["risk_score"]
        )

        # Step 9: Store claim in database
        await self._store_claim(
            claim_number=claim_number,
            incident_id=incident_id,
            passenger_id=passenger_id,
            compensation_calc=compensation_calc,
            approval_decision=approval_decision,
            fraud_assessment=fraud_assessment,
            receipt_analysis=receipt_analysis
        )

        # Step 10: Generate required documents list
        required_docs = self._get_required_documents(
            incident_type=incident_type,
            interim_expenses=interim_expenses,
            declared_value=declared_value
        )

        return {
            "claim_number": claim_number,
            "incident_id": incident_id,
            "eligible": True,
            "compensation_amount": compensation_calc["total_amount"],
            "currency": currency,
            "breakdown": compensation_calc["breakdown"],
            "montreal_convention_limit": MONTREAL_CONVENTION_LIMIT_USD,
            "approval_status": approval_decision["status"],
            "approver_required": approval_decision.get("approver"),
            "auto_approved": approval_decision["status"] == "auto_approved",
            "required_documents": required_docs,
            "fraud_risk_score": fraud_assessment["risk_score"],
            "fraud_indicators": fraud_assessment["indicators"],
            "goodwill_recommendations": goodwill,
            "receipt_analysis": receipt_analysis,
            "processing_timeline": approval_decision["expected_days"],
            "payment_method": "original_payment_method",
            "policy_references": self._get_policy_references(incident_type),
            "next_steps": approval_decision.get("next_steps", [])
        }

    async def _fetch_incident_data(
        self,
        incident_id: str,
        passenger_id: str,
        bag_tag: str
    ) -> Dict[str, Any]:
        """Fetch incident, passenger, and bag data from database."""
        try:
            # Fetch incident
            incident_query = """
                SELECT i.*, b.*, f.flight_number, f.departure_airport, f.arrival_airport
                FROM incidents i
                LEFT JOIN bags b ON i.bag_id = b.id
                LEFT JOIN flights f ON b.flight_id = f.id
                WHERE i.id = $1
                LIMIT 1
            """
            incident = await self.db_connection.fetchrow(incident_query, incident_id)

            # Fetch passenger details
            passenger_query = """
                SELECT *
                FROM passengers
                WHERE id = $1
                LIMIT 1
            """
            passenger = await self.db_connection.fetchrow(passenger_query, passenger_id)

            # Fetch incident history for this passenger
            history_query = """
                SELECT i.*
                FROM incidents i
                LEFT JOIN bags b ON i.bag_id = b.id
                WHERE b.passenger_id = $1
                ORDER BY i.created_at DESC
                LIMIT 10
            """
            history = await self.db_connection.fetch(history_query, passenger_id)

            return {
                "incident": dict(incident) if incident else {},
                "passenger": dict(passenger) if passenger else {},
                "claim_history": [dict(h) for h in history] if history else []
            }

        except Exception as e:
            self.logger.error(f"Error fetching incident data: {e}")
            return {"incident": {}, "passenger": {}, "claim_history": []}

    async def _generate_claim_number(self, incident_id: str) -> str:
        """Generate unique claim number."""
        now = datetime.utcnow()
        date_part = now.strftime("%Y%m%d")

        # Get count of claims today
        try:
            count_query = """
                SELECT COUNT(*)
                FROM compensation_claims
                WHERE DATE(created_at) = CURRENT_DATE
            """
            count = await self.db_connection.fetchval(count_query)
            sequence = str(count + 1).zfill(4)
        except:
            sequence = "0001"

        return f"COMP-{date_part}-{sequence}"

    async def _assess_fraud_risk(
        self,
        passenger_id: str,
        incident_type: str,
        declared_value: float,
        receipts: List[Dict[str, Any]],
        incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess fraud risk for the claim.

        Returns:
            {
                "risk_score": float,  # 0-1
                "risk_level": str,  # low/medium/high/critical
                "indicators": List[str]
            }
        """
        indicators = []
        risk_score = 0.0

        # Check 1: Excessive claims in past year
        claim_history = incident_data.get("claim_history", [])
        claims_this_year = [
            c for c in claim_history
            if datetime.fromisoformat(str(c["created_at"])) > datetime.utcnow() - timedelta(days=365)
        ]

        if len(claims_this_year) >= self.FRAUD_THRESHOLDS["max_claims_per_year"]:
            indicators.append(f"Excessive claims: {len(claims_this_year)} in past year")
            risk_score += 0.3

        # Check 2: Total claimed amount this year
        try:
            total_query = """
                SELECT COALESCE(SUM(cc.approved_amount), 0) as total
                FROM compensation_claims cc
                JOIN incidents i ON cc.incident_id = i.id
                JOIN bags b ON i.bag_id = b.id
                WHERE b.passenger_id = $1
                  AND cc.created_at > NOW() - INTERVAL '1 year'
            """
            total_claimed = await self.db_connection.fetchval(total_query, passenger_id)

            if total_claimed and total_claimed > self.FRAUD_THRESHOLDS["max_total_claimed_per_year"]:
                indicators.append(f"High total claimed: ${total_claimed:.2f} in past year")
                risk_score += 0.25
        except Exception as e:
            self.logger.error(f"Error checking total claimed: {e}")

        # Check 3: Declared value suspicious
        if declared_value > 5000:
            indicators.append(f"Unusually high declared value: ${declared_value}")
            risk_score += 0.15

        # Check 4: Duplicate or similar claims
        if len(claim_history) > 0:
            similar_claims = [
                c for c in claim_history
                if c.get("incident_type") == incident_type
                and datetime.fromisoformat(str(c["created_at"])) > datetime.utcnow() - timedelta(days=180)
            ]
            if len(similar_claims) >= 2:
                indicators.append(f"Similar claims detected: {len(similar_claims)} in 6 months")
                risk_score += 0.2

        # Check 5: Receipt anomalies (if receipts provided)
        if receipts:
            receipt_risk = await self._check_receipt_authenticity(receipts)
            if receipt_risk["suspicious"]:
                indicators.extend(receipt_risk["issues"])
                risk_score += receipt_risk["risk_contribution"]

        # Determine risk level
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.5:
            risk_level = "medium"
        elif risk_score < 0.7:
            risk_level = "high"
        else:
            risk_level = "critical"

        self.logger.info(
            f"Fraud assessment for passenger {passenger_id}: "
            f"risk_level={risk_level}, score={risk_score:.2f}"
        )

        return {
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level,
            "indicators": indicators
        }

    async def _check_receipt_authenticity(
        self,
        receipts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check receipts for fraud indicators."""
        issues = []
        risk_contribution = 0.0

        # Check for duplicate receipts
        receipt_hashes = set()
        for receipt in receipts:
            content_hash = hash(str(receipt.get("content", "")))
            if content_hash in receipt_hashes:
                issues.append("Duplicate receipt detected")
                risk_contribution += 0.2
            receipt_hashes.add(content_hash)

        # Check for unrealistic timestamps
        for receipt in receipts:
            if "date" in receipt:
                try:
                    receipt_date = datetime.fromisoformat(receipt["date"])
                    if receipt_date > datetime.utcnow():
                        issues.append("Future-dated receipt")
                        risk_contribution += 0.15
                except:
                    pass

        # Check for excessive amounts
        total_receipts = sum(r.get("amount", 0) for r in receipts)
        if total_receipts > 2000:
            issues.append(f"Excessive receipt total: ${total_receipts}")
            risk_contribution += 0.1

        return {
            "suspicious": len(issues) > 0,
            "issues": issues,
            "risk_contribution": min(risk_contribution, 0.5)
        }

    async def _check_eligibility(
        self,
        incident_type: str,
        incident_data: Dict[str, Any],
        fraud_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if claim is eligible for compensation.

        Reasons for ineligibility:
        - Critical fraud risk
        - Incident not confirmed
        - Outside time limits
        - Excluded circumstances
        """
        # Check fraud risk
        if fraud_assessment["risk_level"] == "critical":
            return {
                "eligible": False,
                "reason": "Claim flagged for fraud review",
                "next_steps": ["manual_fraud_investigation"]
            }

        # Check if incident is confirmed
        incident = incident_data.get("incident", {})
        if not incident:
            return {
                "eligible": False,
                "reason": "Incident not found in system",
                "next_steps": ["verify_incident_details"]
            }

        # Check time limits (must file within 21 days for most claims)
        if incident.get("created_at"):
            incident_date = datetime.fromisoformat(str(incident["created_at"]))
            days_since = (datetime.utcnow() - incident_date).days

            if days_since > 21 and incident_type != "lost":
                return {
                    "eligible": False,
                    "reason": f"Claim filed too late ({days_since} days, limit 21 days)",
                    "next_steps": ["contact_customer_service"]
                }

        # All checks passed
        return {"eligible": True}

    async def _process_receipts(
        self,
        receipts: List[Dict[str, Any]],
        incident_type: str
    ) -> Dict[str, Any]:
        """
        Process receipts using OCR + LLM for expense categorization.

        Args:
            receipts: List of receipt data (can include images, text, or structured data)
            incident_type: Type of incident

        Returns:
            {
                "total_claimed": float,
                "essential_items": List[Dict],
                "non_essential_items": List[Dict],
                "approved_amount": float,
                "rejected_amount": float,
                "breakdown": List[Dict]
            }
        """
        essential_items = []
        non_essential_items = []
        total_claimed = 0.0
        approved_amount = 0.0
        rejected_amount = 0.0

        for receipt in receipts:
            # Extract receipt data (could be OCR in real implementation)
            amount = receipt.get("amount", 0)
            description = receipt.get("description", "")
            items = receipt.get("items", [description])

            total_claimed += amount

            # Categorize using LLM
            categorization = await self._categorize_expense(
                items=items,
                amount=amount,
                incident_type=incident_type
            )

            if categorization["category"] == "essential":
                essential_items.append({
                    "description": description,
                    "amount": amount,
                    "approved": True,
                    "reasoning": categorization["reasoning"]
                })
                approved_amount += amount
            else:
                non_essential_items.append({
                    "description": description,
                    "amount": amount,
                    "approved": False,
                    "reasoning": categorization["reasoning"]
                })
                rejected_amount += amount

        self.logger.info(
            f"Receipt processing: ${approved_amount:.2f} approved, "
            f"${rejected_amount:.2f} rejected out of ${total_claimed:.2f}"
        )

        return {
            "total_claimed": total_claimed,
            "essential_items": essential_items,
            "non_essential_items": non_essential_items,
            "approved_amount": approved_amount,
            "rejected_amount": rejected_amount,
            "breakdown": essential_items + non_essential_items
        }

    async def _categorize_expense(
        self,
        items: List[str],
        amount: float,
        incident_type: str
    ) -> Dict[str, Any]:
        """
        Use LLM to categorize expense as essential or non-essential.

        Essential items for baggage delay:
        - Toiletries, basic clothing, medications, phone chargers

        Non-essential:
        - Luxury items, entertainment, gifts, expensive electronics
        """
        system_prompt = f"""You are an expense categorization expert for airline baggage claims.

Incident type: {incident_type}

For baggage delay/loss, ESSENTIAL items are:
- Toiletries (toothbrush, toothpaste, deodorant, soap, shampoo)
- Basic clothing (underwear, socks, t-shirts, pants)
- Medications and medical supplies
- Phone charger, basic adapter
- Basic necessities only

NON-ESSENTIAL items are:
- Luxury or designer items
- Expensive electronics
- Jewelry, accessories
- Entertainment items
- Souvenirs, gifts
- Cosmetics, perfume
- Anything over $100 per item (likely not essential)

Categorize the expense and provide brief reasoning.

Return JSON:
{{
    "category": "<essential|non_essential>",
    "reasoning": "<brief explanation>",
    "confidence": <0-1>
}}"""

        items_str = ", ".join(items)
        user_message = f"""Items: {items_str}
Total amount: ${amount}

Categorize this expense."""

        try:
            llm_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.2
            )

            result = self._parse_json_response(llm_response)
            return result

        except Exception as e:
            self.logger.error(f"Error categorizing expense: {e}")
            # Default to non-essential if can't determine
            return {
                "category": "non_essential",
                "reasoning": "Could not determine category",
                "confidence": 0.3
            }

    async def _calculate_compensation(
        self,
        incident_type: str,
        delay_hours: int,
        declared_value: float,
        incident_data: Dict[str, Any],
        receipt_analysis: Optional[Dict[str, Any]],
        currency: str
    ) -> Dict[str, Any]:
        """
        Calculate compensation amount based on incident type and Montreal Convention.

        Returns:
            {
                "total_amount": float,
                "breakdown": Dict[str, float],
                "currency": str,
                "capped_by_montreal": bool
            }
        """
        base_amount = 0.0
        breakdown = {}

        passenger = incident_data.get("passenger", {})
        loyalty_tier = passenger.get("loyalty_tier", "Standard")

        if incident_type == "delayed":
            # Delayed bag compensation: $50-100 per day, max 5 days
            daily_rate = 100 if loyalty_tier in ["Gold", "Platinum", "Diamond"] else 50
            delay_days = max(1, delay_hours // 24)
            delay_days = min(delay_days, 5)  # Cap at 5 days

            base_amount = daily_rate * delay_days
            breakdown["delay_compensation"] = base_amount

            # Add interim expenses if receipts provided
            if receipt_analysis:
                interim_amount = receipt_analysis["approved_amount"]
                # Cap interim expenses at $500 for delays
                interim_amount = min(interim_amount, 500)
                breakdown["interim_expenses"] = interim_amount
                base_amount += interim_amount

        elif incident_type == "lost":
            # Lost baggage: Up to Montreal Convention limit
            # Use declared value or standard liability
            if declared_value > 0:
                base_amount = min(declared_value, MONTREAL_CONVENTION_LIMIT_USD)
                breakdown["declared_value"] = base_amount
            else:
                # Standard liability for undeclared baggage
                base_amount = min(1500, MONTREAL_CONVENTION_LIMIT_USD)
                breakdown["standard_liability"] = base_amount

            # Inconvenience allowance
            inconvenience = 200 if loyalty_tier in ["Gold", "Platinum", "Diamond"] else 100
            breakdown["inconvenience_allowance"] = inconvenience
            base_amount += inconvenience

        elif incident_type == "damaged":
            # Damaged baggage: Repair or replacement value
            if declared_value > 0:
                # Depreciation: 20% off declared value
                depreciated_value = declared_value * 0.8
                base_amount = min(depreciated_value, 1000)
                breakdown["depreciated_value"] = base_amount
            else:
                base_amount = 300  # Standard damage compensation
                breakdown["standard_damage"] = base_amount

        elif incident_type == "pilferage":
            # Items stolen from bag
            if declared_value > 0:
                base_amount = min(declared_value, 1000)
                breakdown["pilferage_claim"] = base_amount
            else:
                base_amount = 500
                breakdown["standard_pilferage"] = base_amount

        # Apply loyalty tier bonus
        tier_multipliers = {
            "Standard": 1.0,
            "Silver": 1.05,
            "Gold": 1.10,
            "Platinum": 1.15,
            "Diamond": 1.20
        }
        tier_multiplier = tier_multipliers.get(loyalty_tier, 1.0)

        if tier_multiplier > 1.0:
            tier_bonus = base_amount * (tier_multiplier - 1.0)
            breakdown["loyalty_tier_bonus"] = tier_bonus
            base_amount += tier_bonus

        # Check Montreal Convention cap
        capped_by_montreal = False
        if base_amount > MONTREAL_CONVENTION_LIMIT_USD:
            breakdown["original_amount"] = base_amount
            breakdown["montreal_convention_cap"] = MONTREAL_CONVENTION_LIMIT_USD
            base_amount = MONTREAL_CONVENTION_LIMIT_USD
            capped_by_montreal = True

        # Currency conversion if needed
        if currency != "USD":
            # In real implementation, would call currency API
            # For now, just note the currency
            breakdown["currency_note"] = f"Amount calculated in USD, will be converted to {currency}"

        return {
            "total_amount": round(base_amount, 2),
            "breakdown": breakdown,
            "currency": currency,
            "capped_by_montreal": capped_by_montreal
        }

    async def _determine_approval_workflow(
        self,
        compensation_amount: float,
        fraud_risk_score: float,
        incident_type: str,
        passenger_tier: str
    ) -> Dict[str, Any]:
        """
        Determine approval workflow based on amount and risk.

        Workflow:
        - < $200 + low fraud risk: Auto-approve
        - $200-500 + low/medium risk: Supervisor approval
        - > $500 or high fraud risk: Manager approval
        - Critical fraud risk: Special investigation

        Returns:
            {
                "status": str,  # auto_approved/pending_supervisor/pending_manager/fraud_investigation
                "approver": str,
                "expected_days": int,
                "next_steps": List[str]
            }
        """
        # Critical fraud risk → investigation
        if fraud_risk_score >= 0.7:
            return {
                "status": "fraud_investigation",
                "approver": "fraud_prevention_team",
                "expected_days": 14,
                "next_steps": [
                    "fraud_team_review",
                    "request_additional_documentation",
                    "passenger_interview_may_be_required"
                ]
            }

        # Amount-based workflow
        if compensation_amount < APPROVAL_THRESHOLDS["auto_approve"] and fraud_risk_score < 0.3:
            return {
                "status": "auto_approved",
                "approver": "system",
                "expected_days": 1,
                "next_steps": [
                    "payment_processing",
                    "confirmation_email_sent"
                ]
            }
        elif compensation_amount < APPROVAL_THRESHOLDS["supervisor"]:
            return {
                "status": "pending_supervisor",
                "approver": "supervisor",
                "expected_days": 3,
                "next_steps": [
                    "supervisor_review_queue",
                    "approval_notification_pending"
                ]
            }
        else:
            # High-value claim or VIP passenger
            if passenger_tier in ["Platinum", "Diamond"]:
                expected_days = 3  # Expedited for VIP
            else:
                expected_days = 5

            return {
                "status": "pending_manager",
                "approver": "manager",
                "expected_days": expected_days,
                "next_steps": [
                    "manager_review_queue",
                    "detailed_documentation_review",
                    "approval_notification_pending"
                ]
            }

    async def _recommend_goodwill_gestures(
        self,
        incident_type: str,
        incident_data: Dict[str, Any],
        compensation_amount: float,
        fraud_risk_score: float
    ) -> List[Dict[str, Any]]:
        """
        Recommend goodwill gestures to improve customer satisfaction.

        Options:
        - Copa Miles
        - Travel vouchers
        - Lounge passes
        - Upgrade certificates
        - Priority boarding
        """
        recommendations = []

        # Don't offer goodwill if fraud risk is high
        if fraud_risk_score > 0.5:
            return recommendations

        passenger = incident_data.get("passenger", {})
        loyalty_tier = passenger.get("loyalty_tier", "Standard")

        # Copa Miles based on incident severity
        if incident_type == "delayed" and compensation_amount < 200:
            miles = int(compensation_amount * COPA_MILES_PER_USD * 0.5)  # 50% bonus in miles
            recommendations.append({
                "type": "copa_miles",
                "amount": miles,
                "description": f"{miles:,} Copa Miles as apology for inconvenience",
                "estimated_value_usd": round(miles / COPA_MILES_PER_USD, 2)
            })

        if incident_type == "lost":
            # Significant goodwill for lost bags
            recommendations.append({
                "type": "travel_voucher",
                "amount": 200,
                "description": "$200 travel voucher for future Copa Airlines flight",
                "expiry": "12 months"
            })

            if loyalty_tier in ["Gold", "Platinum", "Diamond"]:
                recommendations.append({
                    "type": "lounge_passes",
                    "amount": 4,
                    "description": "4 Copa Club lounge passes",
                    "expiry": "12 months"
                })

        if incident_type == "damaged":
            recommendations.append({
                "type": "priority_boarding",
                "amount": 6,
                "description": "Priority boarding on next 6 Copa flights",
                "expiry": "12 months"
            })

        # VIP passengers get enhanced gestures
        if loyalty_tier in ["Platinum", "Diamond"] and incident_type in ["lost", "delayed"]:
            recommendations.append({
                "type": "upgrade_certificate",
                "amount": 1,
                "description": "Complimentary upgrade certificate (Economy to Business)",
                "expiry": "12 months"
            })

        return recommendations

    async def _store_claim(
        self,
        claim_number: str,
        incident_id: str,
        passenger_id: str,
        compensation_calc: Dict[str, Any],
        approval_decision: Dict[str, Any],
        fraud_assessment: Dict[str, Any],
        receipt_analysis: Optional[Dict[str, Any]]
    ):
        """Store compensation claim in database."""
        try:
            insert_query = """
                INSERT INTO compensation_claims (
                    claim_number,
                    incident_id,
                    passenger_id,
                    claimed_amount,
                    approved_amount,
                    currency,
                    approval_status,
                    approver_required,
                    fraud_risk_score,
                    fraud_indicators,
                    breakdown,
                    receipt_analysis,
                    created_at,
                    expected_resolution_date
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """

            await self.db_connection.execute(
                insert_query,
                claim_number,
                incident_id,
                passenger_id,
                compensation_calc["total_amount"],
                compensation_calc["total_amount"] if approval_decision["status"] == "auto_approved" else None,
                compensation_calc["currency"],
                approval_decision["status"],
                approval_decision.get("approver"),
                fraud_assessment["risk_score"],
                json.dumps(fraud_assessment["indicators"]),
                json.dumps(compensation_calc["breakdown"]),
                json.dumps(receipt_analysis) if receipt_analysis else None,
                datetime.utcnow(),
                datetime.utcnow() + timedelta(days=approval_decision["expected_days"])
            )

            self.logger.info(f"Stored claim {claim_number} in database")

        except Exception as e:
            self.logger.error(f"Error storing claim: {e}")

    def _get_required_documents(
        self,
        incident_type: str,
        interim_expenses: bool,
        declared_value: float
    ) -> List[str]:
        """Get list of required documents for claim."""
        docs = [
            "Baggage claim tag (or PIR number)",
            "Flight boarding pass",
            "Government-issued photo ID"
        ]

        if interim_expenses:
            docs.extend([
                "Original receipts for expenses",
                "Bank/credit card statements"
            ])

        if declared_value > 1000:
            docs.extend([
                "Proof of bag contents (receipts, photos)",
                "Proof of value (purchase receipts)"
            ])

        if incident_type == "damaged":
            docs.append("Photos of damaged baggage")

        if incident_type == "pilferage":
            docs.extend([
                "Police report (if filed)",
                "List of missing items with values"
            ])

        return docs

    def _get_policy_references(self, incident_type: str) -> List[str]:
        """Get policy references for claim."""
        references = [
            "Montreal Convention Article 22 (Limits of Liability)",
            "Montreal Convention Article 17 (Liability for Baggage)",
            "Copa Airlines Conditions of Carriage Section 10 (Baggage)"
        ]

        if incident_type == "delayed":
            references.append("Montreal Convention Article 19 (Delay)")
        elif incident_type == "lost":
            references.append("Montreal Convention Article 17(2) (Lost Baggage)")
        elif incident_type == "damaged":
            references.append("Montreal Convention Article 17(2) (Damaged Baggage)")

        return references

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            # Remove markdown code blocks if present
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response was: {response}")
            raise

    async def approve_claim(
        self,
        claim_number: str,
        approver_id: str,
        approved_amount: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a compensation claim.

        Args:
            claim_number: Claim number to approve
            approver_id: ID of person approving
            approved_amount: Amount approved (if different from claimed)
            notes: Approval notes

        Returns:
            Updated claim status
        """
        try:
            # Fetch current claim
            claim_query = """
                SELECT *
                FROM compensation_claims
                WHERE claim_number = $1
                LIMIT 1
            """
            claim = await self.db_connection.fetchrow(claim_query, claim_number)

            if not claim:
                return {"error": "Claim not found"}

            # Update claim
            update_query = """
                UPDATE compensation_claims
                SET
                    approval_status = 'approved',
                    approved_amount = COALESCE($1, claimed_amount),
                    approved_by = $2,
                    approved_at = $3,
                    approval_notes = $4
                WHERE claim_number = $5
                RETURNING *
            """

            updated_claim = await self.db_connection.fetchrow(
                update_query,
                approved_amount,
                approver_id,
                datetime.utcnow(),
                notes,
                claim_number
            )

            self.logger.info(
                f"Claim {claim_number} approved by {approver_id} "
                f"for ${updated_claim['approved_amount']}"
            )

            return {
                "claim_number": claim_number,
                "status": "approved",
                "approved_amount": float(updated_claim["approved_amount"]),
                "approved_by": approver_id,
                "approved_at": updated_claim["approved_at"].isoformat(),
                "next_steps": ["initiate_payment", "send_confirmation_email"]
            }

        except Exception as e:
            self.logger.error(f"Error approving claim: {e}")
            return {"error": str(e)}

    async def reject_claim(
        self,
        claim_number: str,
        approver_id: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """Reject a compensation claim."""
        try:
            update_query = """
                UPDATE compensation_claims
                SET
                    approval_status = 'rejected',
                    approved_by = $1,
                    approved_at = $2,
                    rejection_reason = $3
                WHERE claim_number = $4
                RETURNING *
            """

            updated_claim = await self.db_connection.fetchrow(
                update_query,
                approver_id,
                datetime.utcnow(),
                rejection_reason,
                claim_number
            )

            self.logger.info(f"Claim {claim_number} rejected by {approver_id}")

            return {
                "claim_number": claim_number,
                "status": "rejected",
                "rejection_reason": rejection_reason,
                "rejected_by": approver_id,
                "next_steps": ["send_rejection_notification", "offer_appeal_process"]
            }

        except Exception as e:
            self.logger.error(f"Error rejecting claim: {e}")
            return {"error": str(e)}

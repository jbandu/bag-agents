"""
Customer Service Agent

Handles customer inquiries and generates responses about baggage issues.
Provides conversational interface with multi-channel support.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re
from .base_agent import BaseAgent


# Knowledge base with FAQs
KNOWLEDGE_BASE = {
    "en": {
        "where_is_bag": "To track your bag, I need your bag tag number (10 digits starting with 023). You can find this on your baggage claim receipt.",
        "bag_delayed": "I understand your bag hasn't arrived. Let me check its current location and provide you with an update.",
        "file_claim": "I can help you file a Property Irregularity Report (PIR). This will start the process of locating and delivering your bag.",
        "compensation": "You may be eligible for compensation under the Montreal Convention. I can help you start a claim.",
        "prohibited_items": "Prohibited items in checked baggage include lithium batteries, flammable liquids, and explosives. Please see our full list on the website.",
        "bag_weight": "Standard checked bag allowance is 23kg (50lbs). Additional fees apply for overweight bags.",
        "lost_receipt": "No problem! I can look up your bag using your PNR (booking reference) or ticket number.",
    },
    "es": {
        "where_is_bag": "Para rastrear su maleta, necesito el número de etiqueta (10 dígitos que comienzan con 023). Lo puede encontrar en su recibo de equipaje.",
        "bag_delayed": "Entiendo que su maleta no ha llegado. Permítame verificar su ubicación actual y proporcionarle una actualización.",
        "file_claim": "Puedo ayudarle a presentar un Informe de Irregularidad de Propiedad (PIR). Esto iniciará el proceso de localización y entrega de su maleta.",
        "compensation": "Puede ser elegible para compensación bajo el Convenio de Montreal. Puedo ayudarle a iniciar un reclamo.",
        "prohibited_items": "Los artículos prohibidos en el equipaje facturado incluyen baterías de litio, líquidos inflamables y explosivos.",
        "bag_weight": "El peso estándar de equipaje facturado es 23kg (50lbs). Se aplican tarifas adicionales para maletas con exceso de peso.",
        "lost_receipt": "¡No hay problema! Puedo buscar su maleta usando su PNR (referencia de reserva) o número de boleto.",
    },
    "pt": {
        "where_is_bag": "Para rastrear sua mala, preciso do número da etiqueta (10 dígitos começando com 023). Você pode encontrá-lo no seu recibo de bagagem.",
        "bag_delayed": "Entendo que sua mala não chegou. Deixe-me verificar sua localização atual e fornecer uma atualização.",
        "file_claim": "Posso ajudá-lo a registrar um Relatório de Irregularidade de Propriedade (PIR). Isso iniciará o processo de localização e entrega de sua mala.",
        "compensation": "Você pode ser elegível para compensação sob a Convenção de Montreal. Posso ajudá-lo a iniciar uma reclamação.",
        "prohibited_items": "Itens proibidos na bagagem despachada incluem baterias de lítio, líquidos inflamáveis e explosivos.",
        "bag_weight": "O peso padrão de bagagem despachada é 23kg (50lbs). Taxas adicionais se aplicam para malas com excesso de peso.",
        "lost_receipt": "Sem problema! Posso procurar sua mala usando seu PNR (referência de reserva) ou número do bilhete.",
    }
}


class CustomerServiceAgent(BaseAgent):
    """
    Provides intelligent customer service for baggage-related inquiries.

    Capabilities:
    - Natural language query understanding
    - Baggage tracking and status updates
    - Automated response generation
    - PIR generation
    - Passenger verification
    - Sentiment analysis
    - Intelligent triage and escalation
    - Multi-language support (English, Spanish, Portuguese)
    - Multi-channel support (web chat, WhatsApp, SMS, email)
    """

    def __init__(self, llm_client=None, db_connection=None, config=None):
        """Initialize CustomerServiceAgent."""
        super().__init__(
            agent_name="customer_service_agent",
            llm_client=llm_client,
            db_connection=db_connection,
            config=config
        )

        # Sentiment thresholds
        self.SENTIMENT_THRESHOLDS = {
            "very_negative": 0.2,
            "negative": 0.4,
            "neutral": 0.6,
            "positive": 0.8
        }

        # Auto-resolve vs escalate criteria
        self.AUTO_RESOLVE_QUERIES = [
            "bag_status", "tracking", "location", "eta",
            "general_info", "faq", "policy"
        ]

        self.ESCALATE_QUERIES = [
            "vip_passenger", "high_value_claim", "legal_threat",
            "media_inquiry", "severe_complaint", "safety_concern"
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute customer service interaction.

        Args:
            input_data: Dictionary containing:
                - customer_query: Customer's question/concern
                - bag_tag: Baggage tag number (optional)
                - passenger_id: Passenger identifier (optional)
                - pnr: Booking reference (optional)
                - language: Preferred language (default: en)
                - channel: Communication channel (web_chat, whatsapp, sms, email)
                - conversation_history: Previous messages (optional)
                - passenger_info: Pre-verified passenger info (optional)

        Returns:
            Dictionary containing:
                - response: Generated response text
                - bag_status: Current bag status (if applicable)
                - next_actions: Recommended follow-up actions
                - escalate: Whether to escalate to human agent
                - escalation_reason: Why escalation is needed
                - pir_generated: PIR details if generated
                - sentiment: Detected sentiment
                - intent: Detected query intent
                - confidence: Confidence in response
                - requires_verification: If passenger verification needed
        """
        self.validate_input(input_data, ["customer_query"])

        query = input_data["customer_query"]
        bag_tag = input_data.get("bag_tag")
        passenger_id = input_data.get("passenger_id")
        pnr = input_data.get("pnr")
        language = input_data.get("language", "en")
        channel = input_data.get("channel", "web_chat")
        conversation_history = input_data.get("conversation_history", [])
        passenger_info = input_data.get("passenger_info")

        self.logger.info(
            f"Processing customer query via {channel} in {language}: {query[:100]}..."
        )

        # Step 1: Analyze sentiment
        sentiment_analysis = await self._analyze_sentiment(query, language)

        # Step 2: Detect intent
        intent_analysis = await self._detect_intent(query, language, conversation_history)

        # Step 3: Check if passenger verification is required
        requires_verification = await self._check_verification_required(
            intent_analysis["intent"],
            passenger_info
        )

        if requires_verification and not passenger_info:
            return {
                "response": self._get_verification_message(language),
                "requires_verification": True,
                "intent": intent_analysis["intent"],
                "sentiment": sentiment_analysis["sentiment"],
                "next_actions": ["request_passenger_verification"],
                "escalate": False
            }

        # Step 4: Fetch relevant data
        context_data = await self._fetch_context_data(
            bag_tag=bag_tag,
            passenger_id=passenger_id,
            pnr=pnr,
            intent=intent_analysis["intent"]
        )

        # Step 5: Check if PIR should be generated
        pir_generated = None
        if intent_analysis["intent"] == "file_claim" and bag_tag:
            pir_generated = await self._generate_pir(
                bag_tag=bag_tag,
                passenger_info=passenger_info or {},
                issue_description=query
            )

        # Step 6: Generate response using LLM
        response_data = await self._generate_response(
            query=query,
            intent=intent_analysis,
            sentiment=sentiment_analysis,
            context_data=context_data,
            language=language,
            channel=channel,
            conversation_history=conversation_history,
            pir_generated=pir_generated
        )

        # Step 7: Determine if escalation is needed
        escalation_decision = await self._determine_escalation(
            intent=intent_analysis["intent"],
            sentiment=sentiment_analysis,
            context_data=context_data,
            response_confidence=response_data["confidence"]
        )

        # Step 8: Log interaction
        await self._log_interaction(
            query=query,
            response=response_data["response"],
            intent=intent_analysis["intent"],
            sentiment=sentiment_analysis["sentiment"],
            escalated=escalation_decision["escalate"],
            passenger_id=passenger_id,
            bag_tag=bag_tag,
            channel=channel,
            language=language
        )

        return {
            "response": response_data["response"],
            "bag_status": context_data.get("bag_status"),
            "next_actions": response_data["next_actions"],
            "escalate": escalation_decision["escalate"],
            "escalation_reason": escalation_decision.get("reason"),
            "escalation_priority": escalation_decision.get("priority"),
            "pir_generated": pir_generated,
            "sentiment": sentiment_analysis["sentiment"],
            "sentiment_score": sentiment_analysis["score"],
            "intent": intent_analysis["intent"],
            "intent_confidence": intent_analysis["confidence"],
            "confidence": response_data["confidence"],
            "requires_verification": False,
            "language": language,
            "channel": channel,
            "suggested_followup": response_data.get("suggested_followup")
        }

    async def _analyze_sentiment(
        self,
        query: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of customer query using LLM.

        Returns:
            {
                "sentiment": "very_negative" | "negative" | "neutral" | "positive" | "very_positive",
                "score": float,  # 0-1 scale
                "indicators": List[str]  # Emotional indicators detected
            }
        """
        system_prompt = """You are a sentiment analysis expert for customer service.
Analyze the sentiment of the customer's message and detect emotional indicators.

Consider:
- Tone (angry, frustrated, worried, calm, satisfied)
- Urgency level
- Emotional language
- Complaint severity

Return analysis as JSON:
{
    "sentiment": "<very_negative|negative|neutral|positive|very_positive>",
    "score": <0-1>,
    "indicators": ["<indicator 1>", "<indicator 2>"],
    "urgency": "<low|medium|high|critical>"
}"""

        user_message = f"""Language: {language}
Customer message: "{query}"

Analyze the sentiment."""

        try:
            llm_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.3
            )

            result = self._parse_json_response(llm_response)

            self.logger.info(
                f"Sentiment analysis: {result.get('sentiment')} "
                f"(score: {result.get('score'):.2f})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            # Default to neutral if analysis fails
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "indicators": [],
                "urgency": "medium"
            }

    async def _detect_intent(
        self,
        query: str,
        language: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Detect customer's intent using LLM with conversation context.

        Returns:
            {
                "intent": str,  # Primary intent category
                "sub_intent": str,  # Specific intent
                "confidence": float,
                "entities": Dict[str, Any]  # Extracted entities
            }
        """
        system_prompt = """You are an intent classification expert for baggage customer service.

Classify the customer's intent into one of these categories:
- bag_status: Customer wants to know where their bag is
- file_claim: Customer wants to report a problem or file PIR
- compensation: Customer asking about compensation/reimbursement
- general_info: General questions about policies, procedures
- complaint: Expressing dissatisfaction or complaint
- modification: Want to change something about their bag/booking
- thank_you: Expressing gratitude
- other: Other intents

Also extract key entities:
- bag_tag_number: 10-digit bag tag (e.g., 0230556789)
- flight_number: Flight number (e.g., CM123)
- pnr: Booking reference
- dates: Relevant dates mentioned
- locations: Airports or cities mentioned

Return analysis as JSON:
{
    "intent": "<primary intent>",
    "sub_intent": "<specific intent>",
    "confidence": <0-1>,
    "entities": {
        "bag_tag_number": "<number or null>",
        "flight_number": "<number or null>",
        "pnr": "<pnr or null>",
        "dates": ["<date1>"],
        "locations": ["<location1>"]
    },
    "requires_info": ["<field1>", "<field2>"]  # Missing information needed
}"""

        # Build conversation context
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ]) if conversation_history else ""

        user_message = f"""Language: {language}

{f"Previous conversation:{context}" if context else ""}

Current customer message: "{query}"

Detect the intent and extract entities."""

        try:
            llm_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.2
            )

            result = self._parse_json_response(llm_response)

            self.logger.info(
                f"Intent detected: {result.get('intent')} "
                f"(confidence: {result.get('confidence'):.2f})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error detecting intent: {e}")
            return {
                "intent": "general_info",
                "sub_intent": "unknown",
                "confidence": 0.3,
                "entities": {},
                "requires_info": []
            }

    async def _check_verification_required(
        self,
        intent: str,
        passenger_info: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Check if passenger verification is required before sharing information.

        Verification required for:
        - Bag status queries
        - Filing claims
        - Compensation requests
        - Personal information requests
        """
        verification_required_intents = [
            "bag_status", "file_claim", "compensation", "modification"
        ]

        if intent in verification_required_intents:
            # Check if we already have verified passenger info
            return passenger_info is None

        return False

    def _get_verification_message(self, language: str) -> str:
        """Get passenger verification request message in appropriate language."""
        messages = {
            "en": """For security purposes, I need to verify your identity before I can access your baggage information.

Please provide:
- Your booking reference (PNR) or ticket number
- Last name as it appears on the ticket
- Flight number

Alternatively, you can verify using the verification code sent to your email or phone.""",
            "es": """Por razones de seguridad, necesito verificar su identidad antes de acceder a la información de su equipaje.

Por favor proporcione:
- Su referencia de reserva (PNR) o número de boleto
- Apellido tal como aparece en el boleto
- Número de vuelo

Alternativamente, puede verificar usando el código de verificación enviado a su correo electrónico o teléfono.""",
            "pt": """Por motivos de segurança, preciso verificar sua identidade antes de acessar as informações de sua bagagem.

Por favor, forneça:
- Sua referência de reserva (PNR) ou número do bilhete
- Sobrenome como aparece no bilhete
- Número do voo

Alternativamente, você pode verificar usando o código de verificação enviado para seu e-mail ou telefone."""
        }

        return messages.get(language, messages["en"])

    async def _fetch_context_data(
        self,
        bag_tag: Optional[str] = None,
        passenger_id: Optional[str] = None,
        pnr: Optional[str] = None,
        intent: str = "general_info"
    ) -> Dict[str, Any]:
        """
        Fetch relevant context data from database based on intent.
        """
        context = {}

        try:
            if bag_tag:
                # Fetch bag details
                bag_query = """
                    SELECT
                        b.*,
                        p.name as passenger_name,
                        p.email as passenger_email,
                        p.phone as passenger_phone,
                        p.loyalty_tier,
                        f.flight_number,
                        f.departure_airport,
                        f.arrival_airport,
                        f.scheduled_departure,
                        f.scheduled_arrival,
                        f.status as flight_status
                    FROM bags b
                    LEFT JOIN passengers p ON b.passenger_id = p.id
                    LEFT JOIN flights f ON b.flight_id = f.id
                    WHERE b.tag_number = $1
                    LIMIT 1
                """

                bag_result = await self.db_connection.fetchrow(bag_query, bag_tag)

                if bag_result:
                    context["bag_status"] = dict(bag_result)

                    # Fetch recent events for this bag
                    events_query = """
                        SELECT *
                        FROM bag_events
                        WHERE bag_id = $1
                        ORDER BY timestamp DESC
                        LIMIT 10
                    """
                    events = await self.db_connection.fetch(
                        events_query,
                        bag_result["id"]
                    )
                    context["bag_events"] = [dict(e) for e in events]

                    # Check if there's an active incident
                    incident_query = """
                        SELECT *
                        FROM incidents
                        WHERE bag_id = $1 AND status != 'resolved'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    incident = await self.db_connection.fetchrow(
                        incident_query,
                        bag_result["id"]
                    )
                    if incident:
                        context["active_incident"] = dict(incident)

            if passenger_id or pnr:
                # Fetch passenger details
                passenger_query = """
                    SELECT *
                    FROM passengers
                    WHERE id = $1 OR pnr = $2
                    LIMIT 1
                """
                passenger = await self.db_connection.fetchrow(
                    passenger_query,
                    passenger_id,
                    pnr
                )
                if passenger:
                    context["passenger"] = dict(passenger)

            # Fetch knowledge base articles relevant to intent
            if intent in KNOWLEDGE_BASE.get("en", {}):
                context["knowledge_base_article"] = KNOWLEDGE_BASE["en"][intent]

        except Exception as e:
            self.logger.error(f"Error fetching context data: {e}")

        return context

    async def _generate_pir(
        self,
        bag_tag: str,
        passenger_info: Dict[str, Any],
        issue_description: str
    ) -> Dict[str, Any]:
        """
        Generate Property Irregularity Report (PIR) automatically.

        Returns:
            {
                "pir_number": str,
                "bag_tag": str,
                "issue_type": str,
                "description": str,
                "created_at": str,
                "status": str
            }
        """
        try:
            # Generate PIR number (format: PTY-YYYYMMDD-XXXX)
            now = datetime.utcnow()
            date_part = now.strftime("%Y%m%d")

            # Get count of PIRs today to generate sequence
            count_query = """
                SELECT COUNT(*)
                FROM incidents
                WHERE DATE(created_at) = CURRENT_DATE
            """
            count = await self.db_connection.fetchval(count_query)
            sequence = str(count + 1).zfill(4)

            pir_number = f"PTY-{date_part}-{sequence}"

            # Classify issue type using LLM
            system_prompt = """Classify the baggage issue type from the description.

Issue types:
- delayed: Bag delayed but expected to arrive
- missing: Bag not found/lost
- damaged: Bag arrived damaged
- pilferage: Items missing from bag
- misdirected: Bag sent to wrong destination

Return JSON:
{
    "issue_type": "<type>",
    "severity": "<low|medium|high>",
    "brief_description": "<1 sentence summary>"
}"""

            llm_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=f"Issue description: {issue_description}",
                temperature=0.2
            )

            classification = self._parse_json_response(llm_response)

            # Insert PIR into database
            insert_query = """
                INSERT INTO incidents (
                    pir_number,
                    bag_id,
                    incident_type,
                    description,
                    severity,
                    status,
                    created_at,
                    reported_by
                )
                SELECT
                    $1, b.id, $2, $3, $4, 'open', $5, $6
                FROM bags b
                WHERE b.tag_number = $7
                RETURNING id, pir_number, incident_type, description, created_at, status
            """

            pir_record = await self.db_connection.fetchrow(
                insert_query,
                pir_number,
                classification["issue_type"],
                classification["brief_description"],
                classification["severity"],
                now,
                passenger_info.get("id", "customer_service_agent"),
                bag_tag
            )

            pir_data = {
                "pir_number": pir_number,
                "bag_tag": bag_tag,
                "issue_type": classification["issue_type"],
                "description": classification["brief_description"],
                "severity": classification["severity"],
                "created_at": now.isoformat(),
                "status": "open"
            }

            self.logger.info(f"Generated PIR: {pir_number} for bag {bag_tag}")

            return pir_data

        except Exception as e:
            self.logger.error(f"Error generating PIR: {e}")
            return None

    async def _generate_response(
        self,
        query: str,
        intent: Dict[str, Any],
        sentiment: Dict[str, Any],
        context_data: Dict[str, Any],
        language: str,
        channel: str,
        conversation_history: List[Dict[str, str]],
        pir_generated: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate customer service response using LLM with full context.

        Returns:
            {
                "response": str,
                "confidence": float,
                "next_actions": List[str],
                "suggested_followup": str
            }
        """
        # Build context for LLM
        context_str = self._build_context_string(context_data, language)

        system_prompt = f"""You are a helpful and empathetic Copa Airlines customer service agent.

Language: {language}
Channel: {channel}

Guidelines:
1. Be warm, professional, and empathetic
2. Acknowledge customer's emotions, especially if frustrated or worried
3. Provide clear, specific information
4. Use simple language, avoid jargon
5. Always end with a clear next step or offer to help further
6. If sentiment is negative, prioritize de-escalation
7. For {"WhatsApp or SMS" if channel in ["whatsapp", "sms"] else channel}, keep responses concise
8. For email, provide more detailed information

Baggage status codes:
- checked: Bag checked in at origin
- loaded: Bag loaded on aircraft
- in_transit: Bag is traveling
- transferred: Bag transferred at connection airport
- delivered: Bag ready for pickup
- delayed: Bag delayed
- lost: Bag location unknown
- damaged: Bag arrived damaged

{context_str}

Current situation:
- Customer sentiment: {sentiment["sentiment"]} (urgency: {sentiment.get("urgency", "medium")})
- Intent: {intent["intent"]}
{f"- PIR Generated: {pir_generated['pir_number']}" if pir_generated else ""}

Generate a helpful response that addresses the customer's query."""

        # Build conversation history
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-5:]
        ]) if conversation_history else ""

        user_message = f"""{f"Previous conversation:{history_str}" if history_str else ""}

Customer: {query}

Generate your response."""

        try:
            llm_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.7  # Higher temperature for more natural responses
            )

            # Determine next actions based on intent
            next_actions = self._determine_next_actions(
                intent["intent"],
                context_data,
                pir_generated
            )

            # Generate suggested followup
            suggested_followup = self._generate_followup_suggestion(
                intent["intent"],
                context_data,
                language
            )

            return {
                "response": llm_response.strip(),
                "confidence": 0.85,  # Could be improved with actual confidence scoring
                "next_actions": next_actions,
                "suggested_followup": suggested_followup
            }

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            # Fallback response
            return {
                "response": self._get_fallback_response(language),
                "confidence": 0.3,
                "next_actions": ["escalate_to_human"],
                "suggested_followup": None
            }

    def _build_context_string(
        self,
        context_data: Dict[str, Any],
        language: str
    ) -> str:
        """Build context string for LLM from fetched data."""
        context_parts = []

        if "bag_status" in context_data:
            bag = context_data["bag_status"]
            context_parts.append(f"""Bag Information:
- Tag Number: {bag.get("tag_number")}
- Current Status: {bag.get("status")}
- Current Location: {bag.get("current_location")}
- Destination: {bag.get("destination")}
- Flight: {bag.get("flight_number")} ({bag.get("departure_airport")} → {bag.get("arrival_airport")})
- Passenger: {bag.get("passenger_name")} (Tier: {bag.get("loyalty_tier", "Standard")})""")

        if "bag_events" in context_data and context_data["bag_events"]:
            events = context_data["bag_events"]
            context_parts.append(f"""Recent Bag Events:
{chr(10).join([f"- {e['timestamp']}: {e['event_type']} at {e['location']}" for e in events[:5]])}""")

        if "active_incident" in context_data:
            incident = context_data["active_incident"]
            context_parts.append(f"""Active Incident:
- PIR Number: {incident.get("pir_number")}
- Type: {incident.get("incident_type")}
- Status: {incident.get("status")}
- Created: {incident.get("created_at")}""")

        if "knowledge_base_article" in context_data:
            context_parts.append(f"""Relevant Information:
{context_data["knowledge_base_article"]}""")

        return "\n\n".join(context_parts) if context_parts else "No specific bag information available."

    def _determine_next_actions(
        self,
        intent: str,
        context_data: Dict[str, Any],
        pir_generated: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Determine next actions based on intent and context."""
        actions = []

        if intent == "bag_status":
            actions.extend([
                "monitor_bag_location",
                "send_status_updates"
            ])
            if context_data.get("bag_status", {}).get("status") == "delayed":
                actions.append("check_recovery_options")

        elif intent == "file_claim":
            if pir_generated:
                actions.extend([
                    "pir_filed",
                    "initiate_bag_search",
                    "send_pir_confirmation_email"
                ])
            else:
                actions.append("collect_claim_information")

        elif intent == "compensation":
            actions.extend([
                "review_compensation_eligibility",
                "send_claim_form"
            ])

        elif intent == "complaint":
            actions.extend([
                "log_complaint",
                "flag_for_management_review"
            ])

        # Always offer further assistance
        actions.append("offer_additional_help")

        return actions

    def _generate_followup_suggestion(
        self,
        intent: str,
        context_data: Dict[str, Any],
        language: str
    ) -> Optional[str]:
        """Generate suggested followup question or action."""
        suggestions = {
            "en": {
                "bag_status": "Would you like me to send you updates when your bag status changes?",
                "file_claim": "Would you like information about compensation or interim expenses?",
                "compensation": "Do you have receipts for essential items you purchased?",
                "general_info": "Is there anything specific about our baggage policy you'd like to know?",
            },
            "es": {
                "bag_status": "¿Le gustaría recibir actualizaciones cuando cambie el estado de su maleta?",
                "file_claim": "¿Desea información sobre compensación o gastos provisionales?",
                "compensation": "¿Tiene recibos de artículos esenciales que compró?",
                "general_info": "¿Hay algo específico sobre nuestra política de equipaje que le gustaría saber?",
            },
            "pt": {
                "bag_status": "Gostaria que eu enviasse atualizações quando o status de sua mala mudar?",
                "file_claim": "Gostaria de informações sobre compensação ou despesas provisórias?",
                "compensation": "Você tem recibos de itens essenciais que comprou?",
                "general_info": "Há algo específico sobre nossa política de bagagem que você gostaria de saber?",
            }
        }

        return suggestions.get(language, suggestions["en"]).get(intent)

    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response when LLM fails."""
        responses = {
            "en": "I apologize, but I'm having trouble processing your request right now. Let me connect you with a human agent who can better assist you.",
            "es": "Disculpe, pero tengo problemas para procesar su solicitud en este momento. Permítame conectarlo con un agente humano que pueda ayudarlo mejor.",
            "pt": "Desculpe, mas estou tendo problemas para processar seu pedido no momento. Deixe-me conectá-lo com um agente humano que possa ajudá-lo melhor."
        }
        return responses.get(language, responses["en"])

    async def _determine_escalation(
        self,
        intent: str,
        sentiment: Dict[str, Any],
        context_data: Dict[str, Any],
        response_confidence: float
    ) -> Dict[str, Any]:
        """
        Determine if query should be escalated to human agent.

        Escalation criteria:
        1. Very negative sentiment
        2. Low confidence in response
        3. VIP passenger
        4. High-value claim
        5. Legal/media inquiry
        6. Specific escalation intents
        7. Safety concerns
        """
        escalate = False
        reason = None
        priority = "normal"

        # Check sentiment
        if sentiment["sentiment"] == "very_negative":
            escalate = True
            reason = "Very negative customer sentiment detected"
            priority = "high"

        # Check confidence
        if response_confidence < 0.5:
            escalate = True
            reason = "Low confidence in automated response"
            priority = "medium"

        # Check VIP status
        passenger = context_data.get("passenger", {})
        if passenger.get("loyalty_tier") in ["Gold", "Platinum", "Diamond"]:
            if sentiment["sentiment"] in ["negative", "very_negative"]:
                escalate = True
                reason = f"VIP passenger ({passenger['loyalty_tier']}) with negative sentiment"
                priority = "high"

        # Check intent-based escalation
        if intent in self.ESCALATE_QUERIES:
            escalate = True
            reason = f"Intent requires human attention: {intent}"
            priority = "urgent"

        # Check for legal/safety keywords
        legal_keywords = ["lawyer", "attorney", "sue", "legal action", "lawsuit"]
        safety_keywords = ["injured", "hurt", "dangerous", "safety", "hazard"]

        query_lower = context_data.get("original_query", "").lower()

        if any(keyword in query_lower for keyword in legal_keywords):
            escalate = True
            reason = "Legal inquiry detected"
            priority = "urgent"

        if any(keyword in query_lower for keyword in safety_keywords):
            escalate = True
            reason = "Safety concern detected"
            priority = "urgent"

        # Check urgency
        if sentiment.get("urgency") == "critical":
            escalate = True
            reason = "Critical urgency level"
            priority = "urgent"

        return {
            "escalate": escalate,
            "reason": reason,
            "priority": priority,
            "recommended_department": self._get_recommended_department(intent, reason)
        }

    def _get_recommended_department(
        self,
        intent: str,
        escalation_reason: Optional[str]
    ) -> str:
        """Get recommended department for escalation."""
        if escalation_reason and "legal" in escalation_reason.lower():
            return "legal"
        elif escalation_reason and "safety" in escalation_reason.lower():
            return "safety"
        elif intent == "compensation":
            return "claims"
        elif intent == "complaint":
            return "customer_relations"
        else:
            return "general_support"

    async def _log_interaction(
        self,
        query: str,
        response: str,
        intent: str,
        sentiment: str,
        escalated: bool,
        passenger_id: Optional[str],
        bag_tag: Optional[str],
        channel: str,
        language: str
    ):
        """Log customer service interaction to database."""
        try:
            insert_query = """
                INSERT INTO customer_service_interactions (
                    passenger_id,
                    bag_tag,
                    channel,
                    language,
                    query,
                    response,
                    intent,
                    sentiment,
                    escalated,
                    timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """

            await self.db_connection.execute(
                insert_query,
                passenger_id,
                bag_tag,
                channel,
                language,
                query,
                response,
                intent,
                sentiment,
                escalated,
                datetime.utcnow()
            )

            self.logger.info(
                f"Logged interaction: intent={intent}, sentiment={sentiment}, "
                f"escalated={escalated}, channel={channel}"
            )

        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")

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

    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get summary of a customer service conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Summary including key points, resolution status, sentiment trend
        """
        try:
            query = """
                SELECT *
                FROM customer_service_interactions
                WHERE conversation_id = $1
                ORDER BY timestamp ASC
            """

            interactions = await self.db_connection.fetch(query, conversation_id)

            if not interactions:
                return {"error": "Conversation not found"}

            # Build summary using LLM
            conversation_text = "\n\n".join([
                f"Customer: {i['query']}\nAgent: {i['response']}"
                for i in interactions
            ])

            system_prompt = """Summarize this customer service conversation.

Provide:
1. Main issue/concern
2. Resolution provided
3. Customer sentiment trend (improved/unchanged/worsened)
4. Key action items
5. Follow-up needed (yes/no)

Return as JSON."""

            summary_response = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_message=conversation_text,
                temperature=0.3
            )

            summary = self._parse_json_response(summary_response)

            summary["conversation_id"] = conversation_id
            summary["total_interactions"] = len(interactions)
            summary["duration_minutes"] = (
                interactions[-1]["timestamp"] - interactions[0]["timestamp"]
            ).total_seconds() / 60

            return summary

        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return {"error": str(e)}

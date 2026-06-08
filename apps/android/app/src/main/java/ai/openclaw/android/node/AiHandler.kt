package ai.openclaw.android.node

import android.content.Context
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.content
import ai.openclaw.android.gateway.GatewaySession
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * AiHandler handles on-device LLM requests using Google AI Edge SDK (Gemini Nano).
 * This provides zero-cost, local-first intelligence on supported devices like the Flip5.
 */
class AiHandler(private val context: Context) {

    // Note: "gemini-nano" is the target for on-device execution.
    // For initial emulator testing or non-AICore devices, 
    // developers often use a fallback or the remote "gemini-1.5-flash" 
    // but the final target here is on-device "gemini-nano".
    private val model = GenerativeModel(
        modelName = "gemini-nano",
        apiKey = "LOCAL_ONLY" // AICore handles auth for Nano on-device
    )

    suspend fun handlePrompt(paramsJson: String?): GatewaySession.InvokeResult {
        if (paramsJson == null) {
            return GatewaySession.InvokeResult.error(
                code = "INVALID_REQUEST",
                message = "INVALID_REQUEST: params required"
            )
        }

        return try {
            val json = Json.parseToJsonElement(paramsJson).jsonObject
            val prompt = json["prompt"]?.jsonPrimitive?.content
                ?: return GatewaySession.InvokeResult.error(
                    code = "INVALID_REQUEST",
                    message = "INVALID_REQUEST: 'prompt' field required"
                )

            // Execute inference on-device
            val response = model.generateContent(prompt)
            val text = response.text ?: ""

            GatewaySession.InvokeResult.ok("""{"result":"$text","model":"gemini-nano"}""")
        } catch (e: Exception) {
            GatewaySession.InvokeResult.error(
                code = "AI_INFERENCE_ERROR",
                message = "AI_INFERENCE_ERROR: ${e.message}"
            )
        }
    }
}

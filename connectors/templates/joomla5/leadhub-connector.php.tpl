<?php
define('LEADHUB_SITE_UID', '{{SITE_UID}}');
define('LEADHUB_SECRET', '{{SECRET}}');
define('LEADHUB_CONNECTOR_VERSION', '{{CONNECTOR_VERSION}}');
define('LEADHUB_TARGET_JOOMLA_VERSION', '{{TARGET_JOOMLA_VERSION}}');

error_reporting(0);
ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');

if (!function_exists('hash_equals')) {
    function hash_equals($knownString, $userString) {
        if (!is_string($knownString) || !is_string($userString)) {
            return false;
        }
        if (strlen($knownString) !== strlen($userString)) {
            return false;
        }
        $result = 0;
        for ($i = 0; $i < strlen($knownString); $i++) {
            $result |= ord($knownString[$i]) ^ ord($userString[$i]);
        }
        return $result === 0;
    }
}

function leadhub_json($data, $code = 200) {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function leadhub_param($key, $default = '') {
    return isset($_GET[$key]) ? (string) $_GET[$key] : $default;
}

function leadhub_check_signature($action) {
    $siteUid = leadhub_param('site_uid');
    $ts = leadhub_param('ts');
    $sig = leadhub_param('sig');
    if ($siteUid !== LEADHUB_SITE_UID) {
        leadhub_json(array('status' => 'error', 'code' => 'invalid_site_uid', 'message' => 'Invalid site uid'), 403);
    }
    if (!$ts || abs(time() - (int) $ts) > 600) {
        leadhub_json(array('status' => 'error', 'code' => 'expired_timestamp', 'message' => 'Expired timestamp'), 403);
    }
    $payload = $siteUid . $action;
    if ($action === 'sync') {
        $payload .= leadhub_param('type', 'all') . leadhub_param('since_id', '0');
    }
    $payload .= $ts;
    $expected = hash_hmac('sha256', $payload, LEADHUB_SECRET);
    if (!hash_equals($expected, $sig)) {
        leadhub_json(array('status' => 'error', 'code' => 'invalid_signature', 'message' => 'Invalid request signature'), 403);
    }
}

function leadhub_bootstrap() {
    if (!defined('_JEXEC')) {
        define('_JEXEC', 1);
    }
    $root = dirname(__FILE__);
    if (!defined('JPATH_BASE')) {
        define('JPATH_BASE', $root);
    }
    $defines = JPATH_BASE . '/includes/defines.php';
    $framework = JPATH_BASE . '/includes/framework.php';
    if (file_exists($defines)) {
        require_once $defines;
    }
    if (file_exists($framework)) {
        require_once $framework;
    }
    if (class_exists('\\Joomla\\CMS\\Factory')) {
        return \Joomla\CMS\Factory::getContainer()->get('DatabaseDriver');
    }
    return null;
}

function leadhub_table_exists($db, $table) {
    if (!$db) {
        return false;
    }
    try {
        $name = method_exists($db, 'replacePrefix') ? $db->replacePrefix($table) : str_replace('#__', $db->getPrefix(), $table);
        $db->setQuery("SHOW TABLES LIKE " . $db->quote($name));
        return (bool) $db->loadResult();
    } catch (Throwable $e) {
        return false;
    }
}

function leadhub_load_assoc_list($db, $query) {
    $db->setQuery($query);
    $rows = $db->loadAssocList();
    return is_array($rows) ? $rows : array();
}

function leadhub_sync_rsform($db) {
    if (!leadhub_table_exists($db, '#__rsform_submissions')) {
        return array();
    }
    $sinceId = max(0, (int) leadhub_param('since_id', '0'));
    $submissionsTable = method_exists($db, 'replacePrefix') ? $db->replacePrefix('#__rsform_submissions') : str_replace('#__', $db->getPrefix(), '#__rsform_submissions');
    $valuesTable = method_exists($db, 'replacePrefix') ? $db->replacePrefix('#__rsform_submission_values') : str_replace('#__', $db->getPrefix(), '#__rsform_submission_values');
    $query = "SELECT SubmissionId, FormId, DateSubmitted FROM " . $db->quoteName($submissionsTable) .
        " WHERE SubmissionId > " . (int) $sinceId . " ORDER BY SubmissionId ASC LIMIT 100";
    $submissions = leadhub_load_assoc_list($db, $query);
    $items = array();

    foreach ($submissions as $submission) {
        $submissionId = (int) $submission['SubmissionId'];
        $valueRows = array();
        if (leadhub_table_exists($db, '#__rsform_submission_values')) {
            $valuesQuery = "SELECT FieldName, FieldValue FROM " . $db->quoteName($valuesTable) .
                " WHERE SubmissionId = " . $submissionId;
            $valueRows = leadhub_load_assoc_list($db, $valuesQuery);
        }
        $fields = array();
        foreach ($valueRows as $valueRow) {
            $fields[$valueRow['FieldName']] = $valueRow['FieldValue'];
        }
        $name = isset($fields['name']) ? $fields['name'] : (isset($fields['Name']) ? $fields['Name'] : null);
        $phone = isset($fields['phone']) ? $fields['phone'] : (isset($fields['Phone']) ? $fields['Phone'] : null);
        $email = isset($fields['email']) ? $fields['email'] : (isset($fields['Email']) ? $fields['Email'] : null);
        $message = isset($fields['message']) ? $fields['message'] : (isset($fields['Message']) ? $fields['Message'] : null);
        $items[] = array(
            'external_id' => (string) $submissionId,
            'external_number' => (string) $submissionId,
            'external_created_at' => $submission['DateSubmitted'],
            'customer_name' => $name,
            'customer_phone' => $phone,
            'customer_email' => $email,
            'title' => 'RSForm #' . $submissionId,
            'message' => $message,
            'status' => 'submitted',
            'fields' => $fields
        );
    }
    return $items;
}

function leadhub_sync_virtuemart($db) {
    if (!leadhub_table_exists($db, '#__virtuemart_orders')) {
        return array();
    }
    $sinceId = max(0, (int) leadhub_param('since_id', '0'));
    $ordersTable = method_exists($db, 'replacePrefix') ? $db->replacePrefix('#__virtuemart_orders') : str_replace('#__', $db->getPrefix(), '#__virtuemart_orders');
    $userinfoTable = method_exists($db, 'replacePrefix') ? $db->replacePrefix('#__virtuemart_order_userinfos') : str_replace('#__', $db->getPrefix(), '#__virtuemart_order_userinfos');
    $itemsTable = method_exists($db, 'replacePrefix') ? $db->replacePrefix('#__virtuemart_order_items') : str_replace('#__', $db->getPrefix(), '#__virtuemart_order_items');
    $query = "SELECT virtuemart_order_id, order_number, created_on, order_total, order_currency, order_status FROM " .
        $db->quoteName($ordersTable) . " WHERE virtuemart_order_id > " . (int) $sinceId .
        " ORDER BY virtuemart_order_id ASC LIMIT 100";
    $orders = leadhub_load_assoc_list($db, $query);
    $items = array();

    foreach ($orders as $order) {
        $orderId = (int) $order['virtuemart_order_id'];
        $customer = array();
        if (leadhub_table_exists($db, '#__virtuemart_order_userinfos')) {
            $customerQuery = "SELECT first_name, last_name, phone_1, phone_2, email FROM " . $db->quoteName($userinfoTable) .
                " WHERE virtuemart_order_id = " . $orderId . " AND address_type = " . $db->quote('BT') . " LIMIT 1";
            $customerRows = leadhub_load_assoc_list($db, $customerQuery);
            $customer = isset($customerRows[0]) ? $customerRows[0] : array();
        }
        $orderItems = array();
        if (leadhub_table_exists($db, '#__virtuemart_order_items')) {
            $itemsQuery = "SELECT order_item_sku, order_item_name, product_quantity, product_final_price FROM " .
                $db->quoteName($itemsTable) . " WHERE virtuemart_order_id = " . $orderId;
            $itemRows = leadhub_load_assoc_list($db, $itemsQuery);
            foreach ($itemRows as $itemRow) {
                $orderItems[] = array(
                    'sku' => $itemRow['order_item_sku'],
                    'name' => $itemRow['order_item_name'],
                    'quantity' => $itemRow['product_quantity'],
                    'price' => $itemRow['product_final_price']
                );
            }
        }
        $customerName = trim((isset($customer['first_name']) ? $customer['first_name'] : '') . ' ' . (isset($customer['last_name']) ? $customer['last_name'] : ''));
        $items[] = array(
            'external_id' => (string) $orderId,
            'external_number' => $order['order_number'],
            'external_created_at' => $order['created_on'],
            'customer_name' => $customerName,
            'customer_phone' => isset($customer['phone_1']) && $customer['phone_1'] ? $customer['phone_1'] : (isset($customer['phone_2']) ? $customer['phone_2'] : null),
            'customer_email' => isset($customer['email']) ? $customer['email'] : null,
            'title' => 'VirtueMart #' . $order['order_number'],
            'amount' => $order['order_total'],
            'currency' => $order['order_currency'],
            'status' => $order['order_status'],
            'items' => $orderItems
        );
    }
    return $items;
}

$action = leadhub_param('action', 'ping');
leadhub_check_signature($action);

if ($action === 'ping') {
    leadhub_json(array(
        'status' => 'ok',
        'connector_version' => LEADHUB_CONNECTOR_VERSION,
        'target_joomla_version' => LEADHUB_TARGET_JOOMLA_VERSION,
        'site_uid' => LEADHUB_SITE_UID
    ));
}

$db = leadhub_bootstrap();
if (!$db) {
    leadhub_json(array('status' => 'error', 'code' => 'joomla_bootstrap_failed', 'message' => 'Joomla bootstrap failed'), 500);
}

if ($action === 'discover') {
    leadhub_json(array(
        'status' => 'ok',
        'sources' => array(
            'rsform' => leadhub_table_exists($db, '#__rsform_submissions'),
            'virtuemart' => leadhub_table_exists($db, '#__virtuemart_orders')
        )
    ));
}

if ($action === 'sync') {
    $type = leadhub_param('type', 'all');
    $items = array();
    if ($type === 'rsform' || $type === 'all') {
        $items = array_merge($items, leadhub_sync_rsform($db));
    }
    if ($type === 'virtuemart' || $type === 'all') {
        $items = array_merge($items, leadhub_sync_virtuemart($db));
    }
    leadhub_json(array('status' => 'ok', 'type' => $type, 'items' => $items));
}

leadhub_json(array('status' => 'error', 'code' => 'unknown_action', 'message' => 'Unknown action'), 400);

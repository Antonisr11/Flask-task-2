# ΥΠΟ ΚΑΤΑΣΚΕΥΗ - ΣΥΝΤΟΜΑ ΚΟΝΤΑ ΣΑΣ
# 1η Υποχρεωτική Εργασία Πληροφοριακά Συστήματα

## Περιεχόμενα 
* [Γενικά](#General)
* [Ερώτημα 1](#Create_User) 
* [Ερώτημα 2](#Authentication/Login)
* [Ερώτημα 3](#Search)
* [Ερώτημα 4](#Add_cart)
* [Ερώτημα 5](#Show_cart)
* [Ερώτημα 6](#Remove_cart)
* [Ερώτημα 7](#Buy)
* [Ερώτημα 8](#Show_history)
* [Ερώτημα 9](#Delete_account)
* [Ερώτημα 10](#Create_product)
* [Ερώτημα 11](#Delete_product)
* [Ερώτημα 12](#Update_product)

## General

## Create_User

## Authentication/Login

Η αυθεντικοποίηση του χρήστη έγινε __σχεδόν__ με τον ίδιο τρόπο με την 1η εργασία. Η διαδικασία είναι η εξής:
1. Ο χρήστης κάνει ένα post request στο login με το email του και με τον κωδικό του.
2. Γίνεται έλεγχος αν υπάρχει λογαριασμός με αυτά τα στοιχεία. Αν δεν υπάρχει εμφανίζεται μήνυμα λάθους.
3. Αν υπάρχει καλείται η συνάρτηση create_session που προσθέτει στην λίστα users_sessions μια υπό-λίστα με τα εξής 4 στοιχεία:
	1. Τον μοναδικό user_uuid κωδικό
	2. Το email του χρήστη
	3. Την ώρα εκείνης της στιγμής
	4. Tην κατηγορία του χρήστη (Simple για απλό χρήστη, Admin για διαχειριστή)
4. Επιστρέφεται το user_uuid

Όταν θέλει ο χρήστης να εκτελέσει μια ενέργεια που απαιτεί αυθεντικοποίηση:
1. Καλείται η συνάρτηση is_session_valid 
2. Σαν όρισμα έχουμε το user_uuid του χρήστη και το category __που απαιτεί η ενέργεια αυτή__ (αν η πράξη απαιτεί ο χρήστης να είναι admin το category θα είναι "Admin")
3. Η συνάρτηση επιστρέφει True μόνο αν το user_uuid είναι αποθηκευμένο στην λίστα users_sessions __και__ ο χρήστης έχει το category που απαιτείται. 
	>Πρέπει να σημειώσουμε πως ο Admin έχει και όλα τα δικαιώματα του απλού χρήστη ενώ το αντίστροφο δεν ισχύει. Οπότε αν η πράξη απαιτεί Simple και ο χρήστης είναι Admin, η συνάρτηση θα επιστρέψει True
4. Σε κάθε άλλη περίπτωση η συνάρτηση θα επιστρέψει False

## Search

## Add_cart

## Show_cart

## Remove_cart

## Buy

## Show_history

## Delete_account

## Create_product

## Delete_product

## Update_product


;; TODO: a higher-order language.
;; Then the call creating a higher-order function should
;; residualize to a LET, with the use of it in the body,
;; where references to the created bindings are still in
;; scope.
;; I guess the basic idea would be to lift the `(...)
;; expressions out of the explicit continuations, below.

(define (evaluate fenv e venv g k)
  (let ev ((e e) (g g) (k k))
    (if (symbol? e)
        (k (lookup e venv) g)
        (case (car e)
          ((quote) (k (cadr e) g))
          ((if) (ev (cadr e) (cadr g)
                    (lambda (test g-test)
                      (if test
                          (ev (caddr e) (caddr g)
                              (lambda (value g-value)
                                (k value
                                   `(if ,g-test ,g-value ,(cadddr g)))))
                          (ev (cadddr e) (cadddr g)
                              (lambda (value g-value)
                                (k value
                                   `(if ,g-test ,(caddr g) ,g-value))))))))
          (else 
           (let ()
             (define (apply-rator args g-args)
               (cond ((assq (car e) primitives)
                      => (lambda (pair)
                           (k (apply (cadr pair) args)
                              (cons (car g) g-args))))
                     ((assq (car e) fenv)
                      => (lambda (pair)
                           (let ((params (cadr pair))
                                 (body (caddr pair)))
                             (evaluate fenv body (map list params args) body
                                       (lambda (value g-value)
                                         (k value
                                            `(let ,(map list params g-args)
                                               ,g-value)))))))
                     (else
                      (error "Unknown procedure" e))))
             (let evlis ((rands (cdr e)) (g-rands (cdr g)) (k apply-rator))
               (if (null? rands)
                   (k '() '())
                   (ev (car rands) (car g-rands)
                       (lambda (arg g-arg)
                         (evlis (cdr rands) (cdr g-rands)
                                (lambda (args g-args)
                                  (k (cons arg args)
                                     (cons g-arg g-args))))))))))))))

(define (lookup v env)
  (cond ((assq v env) => cadr)
        (else (error "Unbound variable" v))))

(define primitives
  `((+ ,+) (- ,-) (* ,*) (/ ,/)
    (quotient ,quotient) (remainder ,remainder) (modulo ,modulo)
    (< ,<) (= ,=)
    (not ,not)
    (equal? ,equal?)
    (cons ,cons) (car ,car) (cdr ,cdr) (list ,list) (append ,append)
    (length ,length)
    ))

(define fenv
  '((factorial (n) (if (= n '0)
                       '1
                       (* n (factorial (sub1 n)))))
    (sub1 (x) (- x '1))
    (iterfact (n p) (if (= n '0)
                        p
                        (iterfact (sub1 n) (* n p))))))

(define (testme)
;  (evaluate fenv '(factorial '5) '() '(factorial param)
  (evaluate fenv '(iterfact '5 '1) '() '(iterfact param '1)
            list))
